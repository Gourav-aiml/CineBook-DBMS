"""
Test Database Schema & Constraints
Validates table creation, foreign keys, unique constraints, and normalization integrity in MySQL.
"""

import pytest
from app.db import get_connection, query_all, query_one


def test_database_connection():
    """Verify that the MySQL server is reachable and active."""
    conn = get_connection()
    assert conn.is_connected()
    conn.close()


def test_required_tables_exist():
    """Verify that all 10 normalized tables exist in the cinebook database."""
    tables_result = query_all("SHOW TABLES;")
    table_names = [list(row.values())[0] for row in tables_result]

    expected_tables = [
        "users",
        "movies",
        "cinemas",
        "screens",
        "seats",
        "shows",
        "bookings",
        "booking_seats",
        "seat_locks",
        "payments",
    ]
    for tbl in expected_tables:
        assert tbl in table_names, f"Expected table '{tbl}' was not found in database."


def test_seed_data_counts():
    """Verify that seed data meets the minimum requirements."""
    movies_count = query_one("SELECT COUNT(*) AS count FROM movies;")["count"]
    assert movies_count >= 8, f"Expected at least 8 movies, found {movies_count}."

    cinemas_count = query_one("SELECT COUNT(*) AS count FROM cinemas;")["count"]
    assert cinemas_count >= 3, f"Expected at least 3 cinemas, found {cinemas_count}."

    screens_count = query_one("SELECT COUNT(*) AS count FROM screens;")["count"]
    assert screens_count >= 6, f"Expected at least 6 screens (2 per cinema), found {screens_count}."

    shows_count = query_one("SELECT COUNT(*) AS count FROM shows;")["count"]
    assert shows_count >= 15, f"Expected at least 15 shows, found {shows_count}."

    users_count = query_one("SELECT COUNT(*) AS count FROM users;")["count"]
    assert users_count >= 2, f"Expected at least 2 users, found {users_count}."


def test_double_booking_unique_constraint():
    """
    CRITICAL DBMS TEST:
    Verify that the database itself physically rejects duplicate bookings
    for the same show and seat via the UNIQUE KEY on booking_seats (show_id, seat_id).
    """
    import mysql.connector

    # Fetch an already booked seat for Show 1
    existing = query_one("SELECT booking_id, show_id, seat_id FROM booking_seats WHERE show_id = 1 LIMIT 1;")
    assert existing is not None

    show_id = existing["show_id"]
    seat_id = existing["seat_id"]

    # Create a dummy booking record
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO bookings (user_id, show_id, status, total_amount) VALUES (1, %s, 'CONFIRMED', 250.00)",
            (show_id,),
        )
        new_booking_id = cursor.lastrowid

        # Attempt to insert the already booked seat into the new booking
        with pytest.raises(mysql.connector.Error) as exc_info:
            cursor.execute(
                "INSERT INTO booking_seats (booking_id, show_id, seat_id) VALUES (%s, %s, %s)",
                (new_booking_id, show_id, seat_id),
            )
        
        # Verify it was caught by MySQL's Duplicate Entry constraint (error code 1062)
        assert exc_info.value.errno == 1062, f"Expected duplicate key error 1062, got {exc_info.value.errno}"
    finally:
        conn.rollback()
        cursor.close()
        conn.close()
