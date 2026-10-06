"""
CineBook Application Routes
Handles authentication, movie browsing, show schedules, dynamic seat mapping,
transactional seat locking, and atomic booking confirmations with concurrency control.
"""

from decimal import Decimal
from functools import wraps
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import query_all, query_one, execute_query, db_transaction
import logging

logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)


# -----------------------------------------------------------------------------
# Authentication Helpers
# -----------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to proceed.", "warning")
            return redirect(url_for("main.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# -----------------------------------------------------------------------------
# 1. Home Page
# -----------------------------------------------------------------------------
@main_bp.route("/")
def index():
    query = """
        SELECT 
            m.movie_id,
            m.title,
            m.genre,
            m.language,
            m.duration_minutes,
            m.release_date,
            m.poster_url,
            COUNT(s.show_id) AS upcoming_shows
        FROM movies m
        LEFT JOIN shows s ON m.movie_id = s.movie_id AND s.show_date >= CURRENT_DATE
        GROUP BY m.movie_id, m.title, m.genre, m.language, m.duration_minutes, m.release_date, m.poster_url
        ORDER BY m.movie_id ASC
    """
    movies = query_all(query)
    return render_template("index.html", movies=movies)


# -----------------------------------------------------------------------------
# 2. Authentication: Register, Login, Logout
# -----------------------------------------------------------------------------
@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html")

        existing_user = query_one("SELECT user_id FROM users WHERE email = %s", (email,))
        if existing_user:
            flash("An account with this email already exists. Please log in.", "warning")
            return redirect(url_for("main.login"))

        pwd_hash = generate_password_hash(password)
        try:
            user_id = execute_query(
                "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
                (name, email, pwd_hash),
            )
            session["user_id"] = user_id
            session["user_name"] = name
            session["user_email"] = email
            flash(f"Welcome to CineBook, {name}! Your account has been created.", "success")
            return redirect(url_for("main.index"))
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            flash("Registration failed due to a system error. Please try again.", "danger")
            return render_template("register.html")

    return render_template("register.html")


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        next_url = request.form.get("next") or request.args.get("next")

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("login.html", next_url=next_url)

        user = query_one("SELECT user_id, name, email, password_hash FROM users WHERE email = %s", (email,))
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["user_id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            flash(f"Welcome back, {user['name']}!", "success")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("main.index"))
        else:
            flash("Invalid email or password.", "danger")
            return render_template("login.html", next_url=next_url)

    return render_template("login.html", next_url=request.args.get("next"))


@main_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("main.index"))


# -----------------------------------------------------------------------------
# 3. Movie Details & Show Selection
# -----------------------------------------------------------------------------
@main_bp.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    movie = query_one("SELECT * FROM movies WHERE movie_id = %s", (movie_id,))
    if not movie:
        flash("Movie not found.", "danger")
        return redirect(url_for("main.index"))

    # Fetch distinct dates that have shows for this movie
    dates_query = """
        SELECT DISTINCT show_date 
        FROM shows 
        WHERE movie_id = %s AND show_date >= CURRENT_DATE 
        ORDER BY show_date ASC
    """
    available_dates = [row["show_date"] for row in query_all(dates_query, (movie_id,))]

    selected_date = request.args.get("date")
    if not selected_date and available_dates:
        selected_date = str(available_dates[0])
    elif not selected_date:
        selected_date = None

    # Fetch all shows for this movie on the selected date grouped by cinema
    shows_query = """
        SELECT 
            s.show_id,
            s.show_date,
            s.start_time,
            s.ticket_price,
            sc.screen_id,
            sc.screen_name,
            c.cinema_id,
            c.name AS cinema_name,
            c.address AS cinema_address,
            c.city
        FROM shows s
        JOIN screens sc ON s.screen_id = sc.screen_id
        JOIN cinemas c ON sc.cinema_id = c.cinema_id
        WHERE s.movie_id = %s AND s.show_date = %s
        ORDER BY c.name, s.start_time
    """
    shows = query_all(shows_query, (movie_id, selected_date)) if selected_date else []

    # Organize shows by cinema
    cinemas_map = {}
    for s in shows:
        cid = s["cinema_id"]
        if cid not in cinemas_map:
            cinemas_map[cid] = {
                "cinema_id": cid,
                "cinema_name": s["cinema_name"],
                "cinema_address": s["cinema_address"],
                "city": s["city"],
                "shows": [],
            }
        cinemas_map[cid]["shows"].append(s)

    return render_template(
        "movie.html",
        movie=movie,
        available_dates=available_dates,
        selected_date=selected_date,
        cinemas=list(cinemas_map.values()),
    )


# -----------------------------------------------------------------------------
# 4. Seat Selection Page
# -----------------------------------------------------------------------------
@main_bp.route("/show/<int:show_id>/seats")
def show_seats(show_id):
    show_query = """
        SELECT 
            s.show_id,
            s.show_date,
            s.start_time,
            s.ticket_price,
            m.movie_id,
            m.title AS movie_title,
            m.poster_url,
            sc.screen_id,
            sc.screen_name,
            c.name AS cinema_name
        FROM shows s
        JOIN movies m ON s.movie_id = m.movie_id
        JOIN screens sc ON s.screen_id = sc.screen_id
        JOIN cinemas c ON sc.cinema_id = c.cinema_id
        WHERE s.show_id = %s
    """
    show = query_one(show_query, (show_id,))
    if not show:
        flash("Showtime not found.", "danger")
        return redirect(url_for("main.index"))

    return render_template("seats.html", show=show)


# -----------------------------------------------------------------------------
# 5. Dynamic Seat Availability API (Database-driven Seat State)
# -----------------------------------------------------------------------------
@main_bp.route("/api/show/<int:show_id>/seats")
def api_show_seats(show_id):
    current_user_id = session.get("user_id")

    # Clean up expired seat locks across the system
    execute_query("DELETE FROM seat_locks WHERE expires_at < NOW()")

    seats_query = """
        SELECT 
            st.seat_id,
            st.row_label,
            st.seat_number,
            st.seat_type,
            CASE
                WHEN bs.seat_id IS NOT NULL THEN 'BOOKED'
                WHEN sl.seat_id IS NOT NULL AND sl.expires_at > NOW() AND sl.user_id = %s THEN 'LOCKED_BY_ME'
                WHEN sl.seat_id IS NOT NULL AND sl.expires_at > NOW() THEN 'LOCKED'
                ELSE 'AVAILABLE'
            END AS status
        FROM seats st
        JOIN shows sh ON sh.show_id = %s AND st.screen_id = sh.screen_id
        LEFT JOIN booking_seats bs ON bs.show_id = sh.show_id AND bs.seat_id = st.seat_id
        LEFT JOIN seat_locks sl ON sl.show_id = sh.show_id AND sl.seat_id = st.seat_id AND sl.expires_at > NOW()
        ORDER BY st.row_label ASC, st.seat_number ASC
    """
    seats = query_all(seats_query, (current_user_id or 0, show_id))
    return jsonify({"success": True, "seats": seats})


# -----------------------------------------------------------------------------
# 6. Seat Locking API (Temporary Reservation with 5-minute TTL)
# -----------------------------------------------------------------------------
@main_bp.route("/api/lock-seats", methods=["POST"])
def api_lock_seats():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Please log in before selecting seats."}), 401

    user_id = session["user_id"]
    data = request.get_json() or {}
    show_id = data.get("show_id")
    seat_ids = data.get("seat_ids", [])

    if not show_id or not seat_ids or not isinstance(seat_ids, list):
        return jsonify({"success": False, "error": "Invalid seat selection."}), 400

    try:
        with db_transaction() as conn:
            cursor = conn.cursor(dictionary=True)

            # 1. Prune expired locks
            cursor.execute("DELETE FROM seat_locks WHERE expires_at < NOW()")

            # 2. Check if any selected seat is already confirmed in booking_seats
            format_strings = ",".join(["%s"] * len(seat_ids))
            cursor.execute(
                f"""
                SELECT st.row_label, st.seat_number 
                FROM booking_seats bs
                JOIN seats st ON bs.seat_id = st.seat_id
                WHERE bs.show_id = %s AND bs.seat_id IN ({format_strings})
                """,
                [show_id] + seat_ids,
            )
            booked = cursor.fetchall()
            if booked:
                seat_labels = ", ".join([f"{b['row_label']}{b['seat_number']}" for b in booked])
                return jsonify({
                    "success": False,
                    "error": f"Seat(s) {seat_labels} have already been booked by another user."
                }), 409

            # 3. Check if any selected seat is currently locked by ANOTHER user
            cursor.execute(
                f"""
                SELECT st.row_label, st.seat_number 
                FROM seat_locks sl
                JOIN seats st ON sl.seat_id = st.seat_id
                WHERE sl.show_id = %s 
                  AND sl.seat_id IN ({format_strings})
                  AND sl.user_id != %s
                  AND sl.expires_at > NOW()
                """,
                [show_id] + seat_ids + [user_id],
            )
            locked_others = cursor.fetchall()
            if locked_others:
                seat_labels = ", ".join([f"{l['row_label']}{l['seat_number']}" for l in locked_others])
                return jsonify({
                    "success": False,
                    "error": f"Seat(s) {seat_labels} are temporarily locked by another user. Please choose different seats."
                }), 409

            # 4. Remove previous locks held by THIS user for this show (refreshing selection)
            cursor.execute(
                "DELETE FROM seat_locks WHERE show_id = %s AND user_id = %s",
                (show_id, user_id),
            )

            # 5. Insert new 5-minute locks for the user
            for s_id in seat_ids:
                cursor.execute(
                    """
                    INSERT INTO seat_locks (show_id, seat_id, user_id, locked_at, expires_at)
                    VALUES (%s, %s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 5 MINUTE))
                    """,
                    (show_id, s_id, user_id),
                )

        return jsonify({
            "success": True,
            "message": "Seats locked successfully.",
            "lock_duration_seconds": 300,
        })
    except Exception as e:
        logger.error(f"Error locking seats: {e}")
        return jsonify({"success": False, "error": "Failed to lock seats due to a database error."}), 500


# -----------------------------------------------------------------------------
# 7. Booking Summary Page
# -----------------------------------------------------------------------------
@main_bp.route("/booking/summary")
@login_required
def booking_summary():
    show_id = request.args.get("show_id", type=int)
    seat_ids_raw = request.args.get("seat_ids", "")

    if not show_id or not seat_ids_raw:
        flash("Invalid booking request. Please select your seats.", "warning")
        return redirect(url_for("main.index"))

    try:
        seat_ids = [int(s) for s in seat_ids_raw.split(",") if s.strip()]
    except ValueError:
        flash("Invalid seat parameters.", "danger")
        return redirect(url_for("main.index"))

    if not seat_ids:
        flash("Please select at least one seat.", "warning")
        return redirect(url_for("main.show_seats", show_id=show_id))

    user_id = session["user_id"]

    # Verify that the seats are currently locked by the logged-in user
    format_strings = ",".join(["%s"] * len(seat_ids))
    locks_query = f"""
        SELECT sl.seat_id, st.row_label, st.seat_number, st.seat_type, sl.expires_at
        FROM seat_locks sl
        JOIN seats st ON sl.seat_id = st.seat_id
        WHERE sl.show_id = %s 
          AND sl.user_id = %s 
          AND sl.seat_id IN ({format_strings})
          AND sl.expires_at > NOW()
    """
    valid_locks = query_all(locks_query, [show_id, user_id] + seat_ids)

    if len(valid_locks) != len(seat_ids):
        flash("Your seat lock has expired or is invalid. Please select your seats again.", "danger")
        return redirect(url_for("main.show_seats", show_id=show_id))

    # Fetch show and cinema details
    show = query_one(
        """
        SELECT 
            s.show_id, s.show_date, s.start_time, s.ticket_price,
            m.title AS movie_title, m.poster_url,
            sc.screen_name,
            c.name AS cinema_name, c.address AS cinema_address
        FROM shows s
        JOIN movies m ON s.movie_id = m.movie_id
        JOIN screens sc ON s.screen_id = sc.screen_id
        JOIN cinemas c ON sc.cinema_id = c.cinema_id
        WHERE s.show_id = %s
        """,
        (show_id,),
    )

    ticket_price = Decimal(show["ticket_price"])
    num_tickets = len(valid_locks)
    total_amount = ticket_price * num_tickets

    return render_template(
        "booking_summary.html",
        show=show,
        seats=valid_locks,
        seat_ids_raw=seat_ids_raw,
        num_tickets=num_tickets,
        total_amount=total_amount,
    )


# -----------------------------------------------------------------------------
# 8. Booking Confirmation (Transactional with Concurrency Prevention & 2PL)
# -----------------------------------------------------------------------------
@main_bp.route("/booking/confirm", methods=["POST"])
@login_required
def confirm_booking():
    user_id = session["user_id"]
    show_id = request.form.get("show_id", type=int)
    seat_ids_raw = request.form.get("seat_ids", "")

    if not show_id or not seat_ids_raw:
        flash("Missing booking information.", "danger")
        return redirect(url_for("main.index"))

    try:
        seat_ids = [int(s) for s in seat_ids_raw.split(",") if s.strip()]
    except ValueError:
        flash("Invalid seat parameters.", "danger")
        return redirect(url_for("main.index"))

    if not seat_ids:
        flash("Please select at least one seat.", "warning")
        return redirect(url_for("main.show_seats", show_id=show_id))

    booking_id = None
    try:
        with db_transaction() as conn:
            cursor = conn.cursor(dictionary=True)

            # 1. Prune expired locks
            cursor.execute("DELETE FROM seat_locks WHERE expires_at < NOW()")

            # 2. Pessimistic Row Lock: Acquire row lock on the show to serialize concurrent attempts
            cursor.execute(
                "SELECT show_id, ticket_price FROM shows WHERE show_id = %s FOR UPDATE",
                (show_id,),
            )
            show = cursor.fetchone()
            if not show:
                raise Exception("Show not found.")

            # 3. Check if any seat is already booked in booking_seats
            format_strings = ",".join(["%s"] * len(seat_ids))
            cursor.execute(
                f"""
                SELECT bs.seat_id, st.row_label, st.seat_number 
                FROM booking_seats bs
                JOIN seats st ON bs.seat_id = st.seat_id
                WHERE bs.show_id = %s AND bs.seat_id IN ({format_strings})
                FOR UPDATE
                """,
                [show_id] + seat_ids,
            )
            already_booked = cursor.fetchall()
            if already_booked:
                labels = ", ".join([f"{s['row_label']}{s['seat_number']}" for s in already_booked])
                raise Exception(f"Sorry, seat(s) {labels} have already been booked by another user.")

            # 4. Check user's active locks
            cursor.execute(
                f"""
                SELECT seat_id 
                FROM seat_locks 
                WHERE show_id = %s AND user_id = %s AND seat_id IN ({format_strings}) AND expires_at > NOW()
                FOR UPDATE
                """,
                [show_id, user_id] + seat_ids,
            )
            valid_locks = cursor.fetchall()
            if len(valid_locks) != len(seat_ids):
                raise Exception("Your seat lock has expired. Please select your seats again.")

            # 5. Insert Booking record
            total_amount = Decimal(show["ticket_price"]) * len(seat_ids)
            cursor.execute(
                """
                INSERT INTO bookings (user_id, show_id, booking_time, status, total_amount)
                VALUES (%s, %s, NOW(), 'CONFIRMED', %s)
                """,
                (user_id, show_id, total_amount),
            )
            booking_id = cursor.lastrowid

            # 6. Insert into booking_seats (enforced by UNIQUE KEY uq_show_seat_booked (show_id, seat_id))
            for s_id in seat_ids:
                cursor.execute(
                    """
                    INSERT INTO booking_seats (booking_id, show_id, seat_id)
                    VALUES (%s, %s, %s)
                    """,
                    (booking_id, show_id, s_id),
                )

            # 7. Insert Payment record (Simulated payment success)
            cursor.execute(
                """
                INSERT INTO payments (booking_id, amount, payment_status, payment_time)
                VALUES (%s, %s, 'SUCCESS', NOW())
                """,
                (booking_id, total_amount),
            )

            # 8. Release seat locks
            cursor.execute(
                f"DELETE FROM seat_locks WHERE show_id = %s AND seat_id IN ({format_strings})",
                [show_id] + seat_ids,
            )

        flash("Booking confirmed successfully! Here is your ticket.", "success")
        return redirect(url_for("main.booking_confirmation", booking_id=booking_id))

    except Exception as e:
        logger.error(f"Booking confirmation transaction failed: {e}")
        flash(str(e), "danger")
        return redirect(url_for("main.show_seats", show_id=show_id))


# -----------------------------------------------------------------------------
# 9. Booking Confirmation / Receipt Page
# -----------------------------------------------------------------------------
@main_bp.route("/booking/confirmation/<int:booking_id>")
@login_required
def booking_confirmation(booking_id):
    user_id = session["user_id"]
    query = """
        SELECT 
            b.booking_id,
            b.booking_time,
            b.total_amount,
            b.status AS booking_status,
            u.name AS user_name,
            u.email AS user_email,
            m.title AS movie_title,
            m.poster_url,
            m.language,
            m.genre,
            c.name AS cinema_name,
            c.address AS cinema_address,
            sc.screen_name,
            sh.show_date,
            sh.start_time,
            p.payment_status,
            p.payment_time,
            GROUP_CONCAT(CONCAT(st.row_label, st.seat_number) ORDER BY st.row_label, st.seat_number SEPARATOR ', ') AS seats_list
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        JOIN shows sh ON b.show_id = sh.show_id
        JOIN movies m ON sh.movie_id = m.movie_id
        JOIN screens sc ON sh.screen_id = sc.screen_id
        JOIN cinemas c ON sc.cinema_id = c.cinema_id
        JOIN booking_seats bs ON b.booking_id = bs.booking_id
        JOIN seats st ON bs.seat_id = st.seat_id
        LEFT JOIN payments p ON b.booking_id = p.booking_id
        WHERE b.booking_id = %s AND b.user_id = %s
        GROUP BY 
            b.booking_id, b.booking_time, b.total_amount, b.status,
            u.name, u.email, m.title, m.poster_url, m.language, m.genre,
            c.name, c.address, sc.screen_name, sh.show_date, sh.start_time,
            p.payment_status, p.payment_time
    """
    booking = query_one(query, (booking_id, user_id))
    if not booking:
        flash("Booking not found or unauthorized.", "danger")
        return redirect(url_for("main.index"))

    return render_template("booking_confirmation.html", booking=booking)


# -----------------------------------------------------------------------------
# 10. My Bookings Page
# -----------------------------------------------------------------------------
@main_bp.route("/bookings")
@login_required
def my_bookings():
    user_id = session["user_id"]
    query = """
        SELECT 
            b.booking_id,
            b.booking_time,
            b.total_amount,
            b.status AS booking_status,
            m.title AS movie_title,
            m.poster_url,
            c.name AS cinema_name,
            sc.screen_name,
            sh.show_date,
            sh.start_time,
            p.payment_status,
            GROUP_CONCAT(CONCAT(st.row_label, st.seat_number) ORDER BY st.row_label, st.seat_number SEPARATOR ', ') AS seats_list
        FROM bookings b
        JOIN shows sh ON b.show_id = sh.show_id
        JOIN movies m ON sh.movie_id = m.movie_id
        JOIN screens sc ON sh.screen_id = sc.screen_id
        JOIN cinemas c ON sc.cinema_id = c.cinema_id
        JOIN booking_seats bs ON b.booking_id = bs.booking_id
        JOIN seats st ON bs.seat_id = st.seat_id
        LEFT JOIN payments p ON b.booking_id = p.booking_id
        WHERE b.user_id = %s
        GROUP BY 
            b.booking_id, b.booking_time, b.total_amount, b.status,
            m.title, m.poster_url, c.name, sc.screen_name, sh.show_date, sh.start_time,
            p.payment_status
        ORDER BY b.booking_time DESC
    """
    user_bookings = query_all(query, (user_id,))
    return render_template("bookings.html", bookings=user_bookings)
