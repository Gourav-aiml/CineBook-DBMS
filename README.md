# CineBook — Movie Ticket Booking System

CineBook is an academic Database Management Systems (DBMS) project that implements an end-to-end movie ticket booking system using **Flask and MySQL**. The project demonstrates practical DBMS concepts including relational database design, normalization, constraints, transactions, concurrency control, indexing, joins, and query optimization.

---

## 1. Project Overview

CineBook is a web-based movie ticket booking system designed to demonstrate how DBMS concepts can be applied to a real-world booking application.

The system supports:

* User registration and login
* Movie browsing
* Cinema and show selection
* Interactive seat selection
* Temporary seat locking for approximately 5 minutes
* Booking confirmation
* Simulated payment
* Booking history
* Logout

The main DBMS focus is **data integrity and concurrency-safe booking**.

---

## 2. Key Features

### User Authentication

* User registration and login
* Passwords stored using Werkzeug password hashing
* Flask session-based authentication

### Movie Catalog

The current movie catalog contains:

1. The Odyssey
2. Avengers: Endgame Encore
3. Avengers: Doomsday
4. M.S. Dhoni: The Untold Story
5. 3 Idiots
6. Project Hail Mary
7. Spider-Man: Brand New Day
8. Oppenheimer

Movie information is loaded dynamically from MySQL.

### Cinema and Showtime Navigation

Users can select:

* Movie
* Cinema
* Date
* Show
* Screen

### Interactive Seat Map

The seat map displays:

* Available seats
* Selected seats
* Temporarily locked seats
* Confirmed booked seats

Each screen contains 40 physical seats arranged in rows A–E.

### Temporary Seat Locking

Selected seats can be temporarily held for approximately 5 minutes before confirmation.

### Booking and Simulated Payment

The booking process creates:

* Booking record
* Booking-seat records
* Simulated payment record

The booking operations are performed inside a database transaction.

### Booking History

Users can view their previous bookings, selected seats, show details, and payment status.

---

## 3. Technology Stack

| Component          | Technology                      |
| ------------------ | ------------------------------- |
| Frontend           | HTML5, CSS3, Vanilla JavaScript |
| Backend            | Python 3, Flask                 |
| Database           | MySQL 8+                        |
| Database Connector | mysql-connector-python          |
| Authentication     | Werkzeug password hashing       |
| Testing            | pytest                          |

No React, Node.js, MongoDB, or SQLite is used.

---

## 4. System Architecture

```text
┌─────────────────────────────────────────────┐
│                 User Browser                │
│          HTML + CSS + Vanilla JS            │
└──────────────────────┬──────────────────────┘
                       │ HTTP
                       ▼
┌─────────────────────────────────────────────┐
│              Flask Application              │
│                                             │
│  routes.py → application and booking logic │
│  db.py     → MySQL connection handling     │
└──────────────────────┬──────────────────────┘
                       │
                       │ mysql-connector-python
                       ▼
┌─────────────────────────────────────────────┐
│                 MySQL 8+                    │
│                                             │
│  10 relational tables                      │
│  Primary/Foreign Keys                       │
│  Constraints and indexes                    │
│  Transactions and row locking              │
└─────────────────────────────────────────────┘
```

---

## 5. Database Schema

The `cinebook` database contains 10 main tables:

1. `users` — registered users
2. `movies` — movie information
3. `cinemas` — cinema branches
4. `screens` — screens inside cinemas
5. `seats` — physical seats
6. `shows` — scheduled movie shows
7. `bookings` — booking information
8. `booking_seats` — seats belonging to a booking
9. `seat_locks` — temporary seat locks
10. `payments` — simulated payment records

### Main Relationships

```text
Cinema 1 ─── N Screen
Screen 1 ─── N Seat
Movie 1 ─── N Show
Screen 1 ─── N Show
User 1 ─── N Booking
Show 1 ─── N Booking
Booking 1 ─── N Booking_Seat
Seat 1 ─── N Booking_Seat
Show 1 ─── N Seat_Lock
Booking 1 ─── N Payment
```

---

## 6. Normalization

The database is designed with normalization up to **Third Normal Form (3NF)**.

### 1NF

All attributes contain atomic values.

For example, multiple seats are not stored as:

```text
booking_id | seats
101        | A1,A2,A3
```

Instead, each seat is stored as a separate row in `booking_seats`:

```text
booking_id | show_id | seat_id
101        | 1       | A1
101        | 1       | A2
101        | 1       | A3
```

### 2NF

Non-key attributes depend on the complete key. Relationship-specific data is separated instead of duplicating movie, cinema, screen, or seat information.

### 3NF

Non-key attributes depend only on the key and not on other non-key attributes.

For example:

* Cinema information belongs in `cinemas`
* Screen information belongs in `screens`
* Seat information belongs in `seats`
* Show information belongs in `shows`
* Movie information belongs in `movies`

This reduces update, insertion, and deletion anomalies.

---

## 7. Keys and Constraints

The project uses:

* Primary Keys
* Foreign Keys
* UNIQUE constraints
* NOT NULL constraints
* CHECK constraints
* DEFAULT values
* Appropriate data types and ENUM values

A key constraint is:

```sql
UNIQUE(show_id, seat_id)
```

in `booking_seats`.

This ensures that the same seat cannot be confirmed twice for the same show.

Foreign keys maintain referential integrity between related tables.

---

## 8. Concurrency and Double-Booking Prevention

Preventing double booking is one of the most important database features of CineBook.

The booking workflow uses multiple layers of protection:

### 1. Temporary Seat Locks

A selected seat can be temporarily locked for approximately 5 minutes.

### 2. Database Transactions

Booking-related operations are executed as one logical transaction.

### 3. Row-Level Locking

MySQL uses:

```sql
SELECT ... FOR UPDATE
```

to lock relevant database rows during critical booking operations.

### 4. UNIQUE Constraint

The database contains:

```sql
UNIQUE(show_id, seat_id)
```

in `booking_seats`.

This provides final database-level protection against duplicate confirmed bookings.

If a booking operation fails, the transaction is rolled back.

> The project uses MySQL transactions and row locking, demonstrating the principles of two-phase locking. A custom lock manager is not implemented.

---

## 9. ACID Properties

### Atomicity

A booking either completes successfully or the transaction is rolled back.

### Consistency

Keys, foreign keys, UNIQUE constraints, and other constraints keep the database valid.

### Isolation

Concurrent transactions are isolated so that conflicting booking operations do not incorrectly modify the same seat.

### Durability

After a transaction is committed, the booking data remains stored in the database.

---

## 10. Transactions

A simplified booking transaction is:

```text
BEGIN
   ↓
Check seat availability
   ↓
Lock/check relevant rows
   ↓
Create booking
   ↓
Insert booking_seats
   ↓
Create payment record
   ↓
Remove relevant temporary locks
   ↓
COMMIT
```

If an error occurs:

```text
ROLLBACK
```

This prevents partially completed bookings.

---

## 11. JOINs

Because the database is normalized into multiple related tables, JOIN operations are required to retrieve combined information.

Example:

```sql
SELECT m.title, s.show_date, s.start_time
FROM movies m
JOIN shows s
ON m.movie_id = s.movie_id;
```

Three-table example:

```sql
SELECT s.start_time, sc.screen_name, c.name
FROM shows s
JOIN screens sc
ON s.screen_id = sc.screen_id
JOIN cinemas c
ON sc.cinema_id = c.cinema_id;
```

---

## 12. Indexing and Query Optimization

Important indexes include:

* `users.email`
* `shows(movie_id, show_date)`
* `booking_seats(show_id, seat_id)`
* `seat_locks(show_id, expires_at)`

Indexes reduce unnecessary full-table scans and improve lookup and join performance.

The project also uses MySQL:

```sql
EXPLAIN
```

to inspect query execution plans and understand how MySQL accesses tables and uses indexes.

---

## 13. Installation and Setup

### Prerequisites

* Python 3.11+
* MySQL 8+
* Git

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Copy `.env.example` to `.env` and configure the local MySQL credentials.

Example:

```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your_secret_key

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=cinebook
DB_POOL_SIZE=10
```

The `.env` file is intentionally excluded from GitHub because it contains local credentials.

### Database Setup

Run:

```text
database/schema.sql
database/seed.sql
```

using MySQL.

### Start the Application

```bash
python run.py
```

Open:

```text
http://127.0.0.1:5000
```

---

## 14. Demo Account

The project includes a demo account:

| Name        | Email                | Password      |
| ----------- | -------------------- | ------------- |
| Gourav Saha | `gourav@example.com` | `password123` |

Additional seeded users may also be present for demonstrating booking relationships.

---

## 15. Testing

Run:

```bash
python -m pytest tests/ -v
```

The test suite covers areas including:

* User registration
* Login
* Movie loading
* Movie/cinema/show navigation
* Seat availability
* Temporary seat locking
* Expired lock handling
* Booking workflow
* Already-booked seat handling
* Concurrent booking attempts
* Transaction rollback
* Logout
* Database-level duplicate prevention

The exact number of passing tests should be taken from the current test run rather than hard-coded in the documentation.

---

## 16. Project Structure

```text
CineBook/
├── app/
│   ├── __init__.py
│   ├── db.py
│   ├── routes.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── movie.html
│   │   ├── seats.html
│   │   ├── booking_summary.html
│   │   ├── booking_confirmation.html
│   │   └── bookings.html
│   └── static/
│       ├── css/
│       ├── js/
│       └── images/
│
├── database/
│   ├── schema.sql
│   └── seed.sql
│
├── docs/
│   ├── ER_DIAGRAM.md
│   ├── DATABASE_DESIGN.md
│   ├── DBMS_CONCEPTS.md
│   ├── IMPORTANT_QUERIES.sql
│   ├── INDEXING.md
│   └── QUERY_OPTIMIZATION.md
│
├── tests/
│   ├── test_database.py
│   ├── test_booking.py
│   └── test_concurrency.py
│
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── run.py
```

---

## 17. Important Files

| File                         | Purpose                                                   |
| ---------------------------- | --------------------------------------------------------- |
| `run.py`                     | Starts the Flask application                              |
| `app/routes.py`              | Application routes and booking logic                      |
| `app/db.py`                  | MySQL connection and transaction handling                 |
| `database/schema.sql`        | Database tables, constraints and indexes                  |
| `database/seed.sql`          | Sample database data                                      |
| `docs/ER_DIAGRAM.md`         | ER model and relationships                                |
| `docs/DATABASE_DESIGN.md`    | Database design and normalization                         |
| `docs/DBMS_CONCEPTS.md`      | DBMS concepts applied to the project                      |
| `docs/IMPORTANT_QUERIES.sql` | Important SQL queries                                     |
| `docs/INDEXING.md`           | Indexing discussion                                       |
| `docs/QUERY_OPTIMIZATION.md` | Query optimization and EXPLAIN                            |
| `tests/`                     | Automated project tests                                   |
| `.env.example`               | Safe configuration template                               |
| `.gitignore`                 | Prevents secrets and generated files from being committed |
| `requirements.txt`           | Python dependencies                                       |

---

## 18. Live Demonstration

Recommended demonstration flow:

1. Start Flask with `python run.py`.
2. Open the CineBook homepage.
3. Show the current movie catalog.
4. Login using the Gourav demo account.
5. Select a movie, cinema, date and show.
6. Open the seat map.
7. Select seats and demonstrate temporary locking.
8. Confirm the booking.
9. Show the simulated payment and confirmation.
10. Open My Bookings.
11. If required, show the related database rows in MySQL.

Useful queries during the demonstration:

```sql
SELECT * FROM seat_locks;

SELECT * FROM booking_seats;

SELECT * FROM bookings;

SELECT * FROM payments;
```

---

## 19. Future Scope

Possible future improvements include:

* Real payment gateway integration
* Email/SMS booking notifications
* Stronger production authentication and session security
* Background service for expired-lock cleanup
* Cloud deployment
* Mobile application
* Movie recommendation system
* Dynamic pricing
* Scalable multi-server deployment

---

## 20. Project Scope

CineBook is an academic DBMS project and demonstration system. Payment processing is simulated, and the application is intended to demonstrate database concepts rather than serve as a production cinema platform.

The main objective is to demonstrate how **relational database design, normalization, constraints, transactions, concurrency control, indexing, joins, and query optimization** can be combined in a practical application.
