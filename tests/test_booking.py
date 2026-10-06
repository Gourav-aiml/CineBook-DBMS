"""
End-to-End User Flow & Booking Integration Tests
Verifies authentication, dynamic seat loading, 5-minute locking, booking confirmation,
and seat availability states.
"""

import time
import pytest
from app import create_app
from app.db import execute_query, query_one, query_all


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_01_registration(client):
    """Test 1: Registration works and saves hashed password."""
    unique_email = f"testuser_{int(time.time())}@example.com"
    res = client.post(
        "/register",
        data={
            "name": "Integration Tester",
            "email": unique_email,
            "password": "secretpassword",
            "confirm_password": "secretpassword",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Welcome to CineBook" in res.data

    user = query_one("SELECT * FROM users WHERE email = %s", (unique_email,))
    assert user is not None
    assert user["name"] == "Integration Tester"
    assert user["password_hash"] != "secretpassword"  # Must be hashed


def test_02_login(client):
    """Test 2: Login works with correct credentials and rejects incorrect ones."""
    # Failed login
    res_fail = client.post(
        "/login",
        data={"email": "rahul@example.com", "password": "wrongpassword"},
        follow_redirects=True,
    )
    assert b"Invalid email or password" in res_fail.data

    # Successful login
    res_success = client.post(
        "/login",
        data={"email": "rahul@example.com", "password": "password123"},
        follow_redirects=True,
    )
    assert res_success.status_code == 200
    assert b"Welcome back, Rahul Sharma!" in res_success.data


def test_03_movies_load_from_mysql(client):
    """Test 3: Movies load from MySQL on the home page."""
    res = client.get("/")
    assert res.status_code == 200
    assert b"Now Showing" in res.data
    assert b"Jawan" in res.data
    assert b"Interstellar" in res.data


def test_04_movie_cinema_show_navigation(client):
    """Test 4: Movie -> cinema -> show navigation works."""
    res = client.get("/movie/1")
    assert res.status_code == 200
    assert b"Jawan" in res.data
    assert b"Available Cinemas &amp; Shows" in res.data or b"Available Cinemas & Shows" in res.data
    assert b"PVR INOX South City Mall" in res.data


def test_05_seats_load_dynamically_from_mysql(client):
    """Test 5: Seats load dynamically from MySQL via API."""
    res = client.get("/api/show/1/seats")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    seats = data["seats"]
    assert len(seats) >= 40

    # Seats A1, A2 are booked in seed data
    a1 = next((s for s in seats if s["row_label"] == "A" and s["seat_number"] == 1), None)
    assert a1 is not None
    assert a1["status"] == "BOOKED"


def test_06_and_07_seat_selection_and_locking(client):
    """Test 6 & Test 7: Seat selection and seat locking works."""
    # Log in as Rahul
    client.post("/login", data={"email": "rahul@example.com", "password": "password123"})

    # Find an available seat for Show 2
    res_seats = client.get("/api/show/2/seats")
    avail = [s for s in res_seats.get_json()["seats"] if s["status"] == "AVAILABLE"]
    assert len(avail) >= 2
    seat_ids_to_lock = [avail[0]["seat_id"], avail[1]["seat_id"]]

    # Lock seats
    res_lock = client.post(
        "/api/lock-seats",
        json={"show_id": 2, "seat_ids": seat_ids_to_lock},
    )
    assert res_lock.status_code == 200
    data = res_lock.get_json()
    assert data["success"] is True
    assert data["lock_duration_seconds"] == 300

    # Verify lock exists in database
    locks = query_all("SELECT * FROM seat_locks WHERE show_id = 2 AND seat_id IN (%s, %s)", tuple(seat_ids_to_lock))
    assert len(locks) == 2


def test_08_locked_seats_unavailable_to_another_user(client):
    """Test 8: Locked seats appear as LOCKED and cannot be locked by another user."""
    # User 1 (Rahul) locks a seat for Show 3
    client.post("/login", data={"email": "rahul@example.com", "password": "password123"})
    res_seats = client.get("/api/show/3/seats")
    avail = [s for s in res_seats.get_json()["seats"] if s["status"] == "AVAILABLE"][0]
    target_seat_id = avail["seat_id"]

    client.post("/api/lock-seats", json={"show_id": 3, "seat_ids": [target_seat_id]})

    # User 2 (Priya) logs in using a separate client session
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client_priya:
        client_priya.post("/login", data={"email": "priya@example.com", "password": "password123"})

        # Priya checks seat map: target seat should be LOCKED
        res_priya_seats = client_priya.get("/api/show/3/seats")
        target_in_map = next(s for s in res_priya_seats.get_json()["seats"] if s["seat_id"] == target_seat_id)
        assert target_in_map["status"] == "LOCKED"

        # Priya attempts to lock the same seat: must be rejected with 409 Conflict
        res_lock_attempt = client_priya.post("/api/lock-seats", json={"show_id": 3, "seat_ids": [target_seat_id]})
        assert res_lock_attempt.status_code == 409
        assert "temporarily locked" in res_lock_attempt.get_json()["error"]


def test_09_expired_locks_become_available(client):
    """Test 9: Expired locks are purged and the seat becomes available again."""
    show_id = 4
    res_seats = client.get(f"/api/show/{show_id}/seats")
    avail = [s for s in res_seats.get_json()["seats"] if s["status"] == "AVAILABLE"][0]
    seat_id = avail["seat_id"]

    # Insert an expired lock directly into MySQL (expired 10 minutes ago)
    execute_query("DELETE FROM seat_locks WHERE show_id = %s AND seat_id = %s", (show_id, seat_id))
    execute_query(
        """
        INSERT INTO seat_locks (show_id, seat_id, user_id, locked_at, expires_at)
        VALUES (%s, %s, 1, DATE_SUB(NOW(), INTERVAL 15 MINUTE), DATE_SUB(NOW(), INTERVAL 10 MINUTE))
        """,
        (show_id, seat_id),
    )

    # Calling the seats API should prune expired locks and report seat as AVAILABLE
    res_after = client.get(f"/api/show/{show_id}/seats")
    seat_status = next(s for s in res_after.get_json()["seats"] if s["seat_id"] == seat_id)
    assert seat_status["status"] == "AVAILABLE"


def test_10_and_11_booking_succeeds_and_appears_in_my_bookings(client):
    """Test 10 & Test 11: Booking succeeds for available seats and appears in My Bookings."""
    client.post("/login", data={"email": "rahul@example.com", "password": "password123"})

    show_id = 5
    res_seats = client.get(f"/api/show/{show_id}/seats")
    avail = [s for s in res_seats.get_json()["seats"] if s["status"] == "AVAILABLE"]
    seat_id = avail[0]["seat_id"]

    # Lock seat
    res_lock = client.post("/api/lock-seats", json={"show_id": show_id, "seat_ids": [seat_id]})
    assert res_lock.get_json()["success"] is True

    # Confirm Booking
    res_confirm = client.post(
        "/booking/confirm",
        data={"show_id": show_id, "seat_ids": str(seat_id)},
        follow_redirects=True,
    )
    assert res_confirm.status_code == 200
    assert b"Booking Confirmed!" in res_confirm.data
    assert b"Booking Reference ID" in res_confirm.data

    # Check My Bookings page
    res_bookings = client.get("/bookings")
    assert res_bookings.status_code == 200
    assert b"My Bookings" in res_bookings.data
    assert b"CONFIRMED" in res_bookings.data


def test_12_already_booked_seat_cannot_be_booked(client):
    """Test 12: An already-booked seat cannot be booked or locked."""
    client.post("/login", data={"email": "rahul@example.com", "password": "password123"})

    # Seat A1 on Show 1 is booked in seed data
    seat_a1 = query_one("SELECT seat_id FROM seats WHERE screen_id = 1 AND row_label = 'A' AND seat_number = 1")["seat_id"]

    # Locking should fail
    res_lock = client.post("/api/lock-seats", json={"show_id": 1, "seat_ids": [seat_a1]})
    assert res_lock.status_code == 409
    assert "already been booked" in res_lock.get_json()["error"]

    # Direct booking confirmation attempt should also fail
    res_confirm = client.post(
        "/booking/confirm",
        data={"show_id": 1, "seat_ids": str(seat_a1)},
        follow_redirects=True,
    )
    assert b"already been booked" in res_confirm.data or b"expired" in res_confirm.data


def test_15_logout(client):
    """Test 15: Logout works and clears user session."""
    client.post("/login", data={"email": "rahul@example.com", "password": "password123"})
    res = client.get("/logout", follow_redirects=True)
    assert res.status_code == 200
    assert b"successfully logged out" in res.data
    # Accessing protected page redirects to login
    res_prot = client.get("/bookings", follow_redirects=True)
    assert b"Please log in to proceed" in res_prot.data
