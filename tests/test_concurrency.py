"""
Concurrency & Transaction Rollback Test Suite
Verifies ACID transaction guarantees and concurrency control:
1. Two simultaneous booking attempts for the same seat cannot both succeed (Pessimistic Locking + Unique Constraint).
2. Atomic multi-seat rollback: If one seat in a multi-seat reservation fails, none are booked.
"""

from concurrent.futures import ThreadPoolExecutor
import pytest
from app import create_app
from app.db import get_connection, query_one, query_all, execute_query, db_transaction


def test_13_simultaneous_booking_collision():
    """
    Test 13: Concurrency Race Condition Test.
    Two users simultaneously attempt to book the exact same seat for Show 6.
    Only ONE user must succeed; the other must receive an error.
    """
    show_id = 6

    # Find a free seat for Show 6
    free_seat = query_one(
        """
        SELECT s.seat_id 
        FROM seats s
        JOIN shows sh ON sh.show_id = %s AND s.screen_id = sh.screen_id
        LEFT JOIN booking_seats bs ON bs.show_id = %s AND bs.seat_id = s.seat_id
        WHERE bs.seat_id IS NULL
        LIMIT 1
        """,
        (show_id, show_id),
    )
    assert free_seat is not None
    target_seat_id = free_seat["seat_id"]

    # Clear any leftover locks
    execute_query("DELETE FROM seat_locks WHERE show_id = %s AND seat_id = %s", (show_id, target_seat_id))

    app = create_app()
    app.config["TESTING"] = True

    def attempt_booking(user_email, user_pwd):
        with app.test_client() as client:
            client.post("/login", data={"email": user_email, "password": user_pwd})
            # Lock the seat
            lock_res = client.post("/api/lock-seats", json={"show_id": show_id, "seat_ids": [target_seat_id]})
            # Attempt booking confirmation
            confirm_res = client.post(
                "/booking/confirm",
                data={"show_id": show_id, "seat_ids": str(target_seat_id)},
                follow_redirects=True,
            )
            is_success = b"Booking Confirmed!" in confirm_res.data
            return {
                "user": user_email,
                "lock_status": lock_res.status_code,
                "booking_success": is_success,
                "response_data": confirm_res.data.decode("utf-8", errors="ignore"),
            }

    # Execute both simultaneously using 2 threads
    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(attempt_booking, "rahul@example.com", "password123")
        f2 = executor.submit(attempt_booking, "priya@example.com", "password123")
        res1 = f1.result()
        res2 = f2.result()

    success_count = sum([res1["booking_success"], res2["booking_success"]])

    # EXACTLY ONE must succeed
    assert success_count == 1, (
        f"Concurrency failure: Expected exactly 1 booking to succeed, but {success_count} succeeded. "
        f"Result 1: {res1['booking_success']}, Result 2: {res2['booking_success']}"
    )

    # Verify that in MySQL database, the seat was recorded exactly ONCE in booking_seats
    booked_count = query_one(
        "SELECT COUNT(*) AS count FROM booking_seats WHERE show_id = %s AND seat_id = %s",
        (show_id, target_seat_id),
    )["count"]
    assert booked_count == 1, f"Database has {booked_count} records for seat {target_seat_id}, expected 1."


def test_14_atomic_multi_seat_rollback():
    """
    Test 14: Atomic Transaction & Rollback Guarantee.
    When a customer attempts to book multiple seats (e.g. S1, S2, S3) and S2
    is already booked, S1 and S3 MUST NOT remain booked.
    The entire transaction must roll back cleanly to maintain database consistency.
    """
    show_id = 7

    # Find 3 available seats for Show 7
    seats = query_all(
        """
        SELECT s.seat_id, s.row_label, s.seat_number 
        FROM seats s
        JOIN shows sh ON sh.show_id = %s AND s.screen_id = sh.screen_id
        LEFT JOIN booking_seats bs ON bs.show_id = %s AND bs.seat_id = s.seat_id
        WHERE bs.seat_id IS NULL
        LIMIT 3
        """,
        (show_id, show_id),
    )
    assert len(seats) == 3

    seat_1 = seats[0]["seat_id"]
    seat_2 = seats[1]["seat_id"]
    seat_3 = seats[2]["seat_id"]

    # Pre-book seat_2 by another user directly in database
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bookings (user_id, show_id, status, total_amount) VALUES (2, %s, 'CONFIRMED', 400.00)",
        (show_id,),
    )
    foreign_booking_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO booking_seats (booking_id, show_id, seat_id) VALUES (%s, %s, %s)",
        (foreign_booking_id, show_id, seat_2),
    )
    conn.commit()
    cursor.close()
    conn.close()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        # Rahul logs in and attempts to book [seat_1, seat_2, seat_3]
        client.post("/login", data={"email": "rahul@example.com", "password": "password123"})

        # Try confirming all 3 seats
        res = client.post(
            "/booking/confirm",
            data={"show_id": show_id, "seat_ids": f"{seat_1},{seat_2},{seat_3}"},
            follow_redirects=True,
        )

        # Booking must fail
        assert b"Booking Confirmed!" not in res.data
        assert b"already been booked" in res.data or b"expired" in res.data

        # CRITICAL VERIFICATION:
        # Neither seat_1 nor seat_3 must exist in booking_seats for Rahul!
        orphan_seat_1 = query_one(
            "SELECT COUNT(*) AS count FROM booking_seats WHERE show_id = %s AND seat_id = %s",
            (show_id, seat_1),
        )["count"]
        orphan_seat_3 = query_one(
            "SELECT COUNT(*) AS count FROM booking_seats WHERE show_id = %s AND seat_id = %s",
            (show_id, seat_3),
        )["count"]

        assert orphan_seat_1 == 0, "Rollback failure: Seat 1 remained booked after partial failure!"
        assert orphan_seat_3 == 0, "Rollback failure: Seat 3 remained booked after partial failure!"
