# CineBook — Movie Ticket Booking System

A complete, production-grade college Database Management Systems (DBMS) project implementing an end-to-end Movie Ticket Booking System with a real MySQL 8.0 backend, Flask application server, transactional seat locking, and concurrency control.

---

## 1. Project Overview

**CineBook** is an interactive web-based cinema ticket reservation platform designed to demonstrate foundational and advanced DBMS concepts:
- Relational schema modeling in **Third Normal Form (3NF)**.
- Real-time seat allocation with **5-minute optimistic/pessimistic seat locking**.
- **ACID Transaction Management** guaranteeing atomic multi-seat checkouts.
- Storage-engine level **Double-Booking Prevention** enforced via MySQL unique constraints and row-level locks.
- B-Tree index optimization and execution plan profiling (`EXPLAIN`).

---

## 2. Key Features

- **User Authentication:** Registration and login secured with `Werkzeug` password hashing (`scrypt`) and session state.
- **Dynamic Catalog:** Browse now-showing movies across genres, languages, and durations loaded directly from MySQL.
- **Multiplex & Showtime Navigation:** Filter schedules by cinema location, date, and auditorium/screen.
- **Interactive Seat Map:** Visual screen indicator and seat grid (Rows A–E, Seats 1–8) with live color-coded states:
  - 🟩 **Available** (Unallocated)
  - 🟦 **Selected** (Currently selected by user)
  - 🟨 **Temporarily Locked** (Held by a user for 5 minutes)
  - 🟥 **Booked** (Confirmed reservation)
- **Temporary Seat Locking:** 5-minute countdown reservation lock to prevent race conditions during checkout.
- **Atomic Booking & Simulated Payment:** Instant checkout and receipt generation.
- **My Bookings History:** View previous reservations with seats list and payment status.

---

## 3. Technology Stack

- **Frontend:** HTML5, CSS3 (Modern Cinema dark interface), Vanilla JavaScript (No React/Node.js).
- **Backend:** Python 3.11+, Flask.
- **Database:** MySQL 8.0+ (InnoDB Storage Engine).
- **Database Connector:** `mysql-connector-python` (Connection pooling & explicit transactions).
- **Testing:** `pytest` (Unit, integration, and multi-threaded concurrency suites).

---

## 4. System Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Browser Client                       │
│    (HTML5 / Modern Dark CSS / Vanilla JS - seats.js)   │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP (Jinja2 & REST APIs)
                            ▼
┌────────────────────────────────────────────────────────┐
│                  Flask Application                     │
│    - app/routes.py (Auth, Catalog, Booking logic)      │
│    - app/db.py (Connection Pool & db_transaction CM)   │
└───────────────────────────┬────────────────────────────┘
                            │ mysql-connector-python
                            ▼
┌────────────────────────────────────────────────────────┐
│               MySQL 8.0 (InnoDB Engine)                │
│    - 10 Normalized Relations (3NF)                     │
│    - Clustered & Secondary B-Tree Indexes              │
│    - Pessimistic Row Locking (SELECT ... FOR UPDATE)   │
│    - Hard Storage Invariant: UNIQUE(show_id, seat_id)  │
└────────────────────────────────────────────────────────┘
```

---

## 5. Database Schema & Tables

The schema is partitioned across 10 tables in `cinebook` database:

1. `users` — Registered customer accounts (`user_id`, `name`, `email`, `password_hash`, `created_at`).
2. `movies` — Feature film details (`movie_id`, `title`, `genre`, `language`, `duration_minutes`, `release_date`, `poster_url`).
3. `cinemas` — Multiplex venues (`cinema_id`, `name`, `address`, `city`).
4. `screens` — Auditoriums per cinema (`screen_id`, `cinema_id`, `screen_name`, `capacity`).
5. `seats` — Physical seats per auditorium (`seat_id`, `screen_id`, `row_label`, `seat_number`, `seat_type`).
6. `shows` — Scheduled showtimes (`show_id`, `movie_id`, `screen_id`, `show_date`, `start_time`, `ticket_price`).
7. `bookings` — Reservation headers (`booking_id`, `user_id`, `show_id`, `booking_time`, `status`, `total_amount`).
8. `booking_seats` — Junction relation allocating seats to bookings (`booking_id`, `show_id`, `seat_id`).
   - **Critical Invariant:** `UNIQUE KEY uq_show_seat_booked (show_id, seat_id)`.
9. `seat_locks` — Temporary 5-minute reservations (`lock_id`, `show_id`, `seat_id`, `user_id`, `locked_at`, `expires_at`).
10. `payments` — Simulated payment settlements (`payment_id`, `booking_id`, `amount`, `payment_status`, `payment_time`).

---

## 6. Normalization & Relational Integrity

- **1NF (First Normal Form):** Every field stores atomic data. Multi-seat selections are NEVER stored as comma-separated values; they are decomposed into `booking_seats`.
- **2NF (Second Normal Form):** In tables with composite keys like `booking_seats (booking_id, seat_id)`, non-key attributes depend on the full composite key. Movie titles and seat coordinates are not stored redundantly.
- **3NF (Third Normal Form):** No transitive dependencies exist. Cinema metadata belongs in `cinemas`, screens in `screens`, shows in `shows`. Modifying a cinema address never causes an update anomaly across show schedules.

---

## 7. Concurrency & Double-Booking Prevention

Double-booking is prevented through three defensive layers:

1. **Temporary Reservation Locks (`seat_locks`):** When a user selects seats, they are locked for 300 seconds. Expired locks are automatically purged before each query.
2. **Pessimistic Row Locking (`SELECT ... FOR UPDATE`):** During booking confirmation, the show row and target seats are exclusively locked in MySQL to serialize concurrent booking requests.
3. **Database Hard Constraint:** `UNIQUE KEY (show_id, seat_id)` in `booking_seats` ensures that even under simultaneous concurrent race conditions, InnoDB will physically reject duplicate writes with MySQL Error 1062, forcing a clean transaction `ROLLBACK`.

---

## 8. Installation & Setup Instructions

### Prerequisites
- Python 3.11+
- MySQL Server 8.0+ running on `localhost:3306`

### 1. Clone or Open the Workspace
```bash
cd CineBook
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure MySQL Database
Create the database schema and seed sample data using the MySQL command-line client:
```powershell
# Windows PowerShell
Get-Content database/schema.sql | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
Get-Content database/seed.sql   | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```
*(Enter your MySQL root password when prompted)*

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and enter your database password:
```ini
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=cinebook_secret_key_12345

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password_here
DB_NAME=cinebook
DB_POOL_SIZE=10
```

---

## 9. Running the Application

Start the Flask local development server:
```bash
python run.py
```
Open your web browser and navigate to:
**`http://127.0.0.1:5000`**

---

## 10. Demo User Accounts

The database comes pre-seeded with 3 demo accounts (all passwords are `password123`):

| Name | Email | Password | Role |
| :--- | :--- | :--- | :--- |
| **Rahul Sharma** | `rahul@example.com` | `password123` | Customer (has initial bookings on Jawan) |
| **Priya Patel** | `priya@example.com` | `password123` | Customer (has initial bookings on Jawan) |
| **Gourav Saha** | `gourav@example.com` | `password123` | Customer / Admin |

---

## 11. Automated Testing

Run the complete test suite with `pytest` to verify all 15 project test scenarios:
```bash
python -m pytest tests/ -v
```

### Summary of Automated Tests:
- `test_01_registration`: Tests user registration with password hashing.
- `test_02_login`: Tests credential verification and session management.
- `test_03_movies_load_from_mysql`: Tests dynamic movie catalog retrieval.
- `test_04_movie_cinema_show_navigation`: Tests movie -> cinema -> showtime filtering.
- `test_05_seats_load_dynamically_from_mysql`: Verifies real-time seat availability calculation.
- `test_06_and_07_seat_selection_and_locking`: Tests temporary 5-minute reservation locking.
- `test_08_locked_seats_unavailable_to_another_user`: Verifies locked seats cannot be hijacked.
- `test_09_expired_locks_become_available`: Verifies automatic pruning of expired locks.
- `test_10_and_11_booking_succeeds_and_appears_in_my_bookings`: Verifies end-to-end booking.
- `test_12_already_booked_seat_cannot_be_booked`: Verifies rejection of booked seats.
- `test_13_simultaneous_booking_collision`: Tests multi-threaded race conditions (only 1 succeeds).
- `test_14_atomic_multi_seat_rollback`: Verifies full transaction rollback on partial failure.
- `test_15_logout`: Tests session termination.
- `test_double_booking_unique_constraint`: Tests MySQL storage-engine level duplicate prevention.

---

## 12. Project Folder Structure

```
CineBook/
├── app/
│   ├── __init__.py           # Flask app factory & Jinja2 custom filters
│   ├── routes.py             # Route controllers & transaction business logic
│   ├── db.py                 # MySQL connection pooling & transaction context manager
│   │
│   ├── templates/
│   │   ├── base.html         # Base layout with navbar & flash alerts
│   │   ├── index.html        # Home page showing movie catalog
│   │   ├── login.html        # User login form
│   │   ├── register.html     # User registration form
│   │   ├── movie.html        # Movie details, cinema & date selector
│   │   ├── seats.html        # Interactive seat grid & countdown timer
│   │   ├── booking_summary.html      # Order summary & pricing breakdown
│   │   ├── booking_confirmation.html # Ticket confirmation receipt
│   │   └── bookings.html     # User booking history
│   │
│   └── static/
│       ├── css/style.css     # Modern cinema dark UI styles
│       └── js/seats.js       # Dynamic seat selection & lock polling
│
├── database/
│   ├── schema.sql            # 10 normalized tables, constraints, indexes
│   └── seed.sql              # Realistic seed data (movies, cinemas, seats, shows)
│
├── docs/
│   ├── ER_DIAGRAM.md         # Mermaid ER diagram & cardinalities
│   ├── DATABASE_DESIGN.md    # 1NF, 2NF, 3NF proofs & functional dependencies
│   ├── DBMS_CONCEPTS.md      # ACID properties, 2PL theory, row-locking
│   ├── IMPORTANT_QUERIES.sql # JOINs, aggregations, GROUP BY & HAVING queries
│   ├── INDEXING.md           # B-Tree index analysis & read-write trade-offs
│   └── QUERY_OPTIMIZATION.md # Real MySQL EXPLAIN execution plans
│
├── tests/
│   ├── test_database.py      # Schema and constraint verification
│   ├── test_booking.py       # End-to-end booking flow tests
│   └── test_concurrency.py   # Multi-threaded race condition & rollback tests
│
├── .env.example              # Environment variables template
├── .gitignore                # Protects secrets, cache, and virtualenvs
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
└── run.py                    # Application launch script
```

---

## 13. Viva Demonstration Guide for Professors

When presenting CineBook to your DBMS professor or external examiner:

1. **Demonstrate 3NF Normalization:** Open `docs/DATABASE_DESIGN.md` and explain how `booking_seats` eliminates repeating groups (1NF), removes partial dependencies (2NF), and separates movies/cinemas/screens/shows to eliminate transitive dependencies (3NF).
2. **Demonstrate the Relational ER Diagram:** Show `docs/ER_DIAGRAM.md` with cardinalities (`1:N` between Cinema and Screens, `1:N` between Screen and Seats, and associative entity `booking_seats`).
3. **Demonstrate Live Seat State (No Hardcoding):** Open `/show/1/seats` in the browser and open MySQL Workbench or CLI side-by-side. Run `SELECT * FROM booking_seats WHERE show_id = 1;` and show that seats `A1` and `A2` are marked red (`BOOKED`) purely because they exist in the database table.
4. **Demonstrate ACID & Concurrency:** Run `python -m pytest tests/test_concurrency.py -v`. Show how two threads simultaneously competing for the exact same seat results in exactly 1 booking and 1 failure, with zero partial states.
5. **Demonstrate Query Optimization:** Show `docs/QUERY_OPTIMIZATION.md` with actual `EXPLAIN` execution plans highlighting `Using index` and `type: eq_ref`.
