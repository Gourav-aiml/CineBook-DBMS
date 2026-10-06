# CineBook — Entity Relationship (ER) Diagram

This document presents the Entity-Relationship (ER) model for the **CineBook** Movie Ticket Booking System.

---

## 1. Mermaid ER Diagram

```mermaid
erDiagram
    USERS ||--o{ BOOKINGS : places
    USERS ||--o{ SEAT_LOCKS : holds
    MOVIES ||--o{ SHOWS : features
    CINEMAS ||--o{ SCREENS : contains
    SCREENS ||--o{ SEATS : has
    SCREENS ||--o{ SHOWS : hosts
    SHOWS ||--o{ BOOKINGS : booked_for
    SHOWS ||--o{ BOOKING_SEATS : scheduled_in
    SHOWS ||--o{ SEAT_LOCKS : locks_held_in
    BOOKINGS ||--|{ BOOKING_SEATS : contains
    BOOKINGS ||--|| PAYMENTS : settled_by
    SEATS ||--o{ BOOKING_SEATS : allocated_to
    SEATS ||--o{ SEAT_LOCKS : temporarily_locked_as

    USERS {
        int user_id PK
        string name
        string email UK
        string password_hash
        datetime created_at
    }

    MOVIES {
        int movie_id PK
        string title
        text description
        string genre
        string language
        int duration_minutes
        date release_date
        string poster_url
        datetime created_at
    }

    CINEMAS {
        int cinema_id PK
        string name
        string address
        string city
    }

    SCREENS {
        int screen_id PK
        int cinema_id FK
        string screen_name
        int capacity
    }

    SEATS {
        int seat_id PK
        int screen_id FK
        string row_label
        int seat_number
        enum seat_type
    }

    SHOWS {
        int show_id PK
        int movie_id FK
        int screen_id FK
        date show_date
        time start_time
        time end_time
        decimal ticket_price
    }

    BOOKINGS {
        int booking_id PK
        int user_id FK
        int show_id FK
        datetime booking_time
        enum status
        decimal total_amount
    }

    BOOKING_SEATS {
        int booking_id PK, FK
        int seat_id PK, FK
        int show_id FK, UK
    }

    SEAT_LOCKS {
        int lock_id PK
        int show_id FK, UK
        int seat_id FK, UK
        int user_id FK
        datetime locked_at
        datetime expires_at
    }

    PAYMENTS {
        int payment_id PK
        int booking_id FK
        decimal amount
        enum payment_status
        datetime payment_time
    }
```

---

## 2. Entity Descriptions & Cardinalities

### 1. `USERS` to `BOOKINGS` (1 : N)
- **One User** can make **zero or many Bookings** over time.
- **Each Booking** must belong to **exactly one User**.
- Cardinality: `1 : N` (One-to-Many).

### 2. `CINEMAS` to `SCREENS` (1 : N)
- **One Cinema** multiplex contains **one or many Screens** (Auditoriums).
- **Each Screen** belongs strictly to **one Cinema**.
- Cardinality: `1 : N`.

### 3. `SCREENS` to `SEATS` (1 : N)
- **One Screen** contains **multiple physical Seats** (e.g., Rows A–E, Seats 1–8).
- **Each Seat** physically belongs to **one Screen**.
- Cardinality: `1 : N`.
- Uniqueness constraint: `UNIQUE (screen_id, row_label, seat_number)`.

### 4. `MOVIES` to `SHOWS` (1 : N)
- **One Movie** can be scheduled for **zero or many Shows** across various dates, screens, and multiplexes.
- **Each Show** features **exactly one Movie**.
- Cardinality: `1 : N`.

### 5. `SCREENS` to `SHOWS` (1 : N)
- **One Screen** can host **many Shows** over different time slots.
- **Each Show** takes place in **exactly one Screen**.
- Cardinality: `1 : N`.
- Uniqueness constraint: `UNIQUE (screen_id, show_date, start_time)`.

### 6. `SHOWS` to `BOOKINGS` (1 : N)
- **One Show** can receive **many Bookings** from different patrons until auditorium capacity is reached.
- **Each Booking** is made for **one specific Show**.
- Cardinality: `1 : N`.

### 7. `BOOKINGS` to `BOOKING_SEATS` (1 : N)
- **One Booking** can include **one or more Seats** (e.g., booking tickets for a family).
- `BOOKING_SEATS` resolves the many-to-many relationship between `BOOKINGS` and `SEATS`.
- Cardinality: `1 : N`.

### 8. `SEATS` to `BOOKING_SEATS` (1 : N)
- A physical **Seat** can appear across multiple bookings over history, but for a specific show it is strictly unique:
- **Critical DBMS Invariant:** `UNIQUE (show_id, seat_id)` guarantees that no physical seat can be confirmed in more than one booking for the same show.

### 9. `BOOKINGS` to `PAYMENTS` (1 : 1)
- **Each Booking** produces **one simulated Payment record**.
- Cardinality: `1 : 1` (One-to-One).

### 10. `SHOWS` and `SEATS` to `SEAT_LOCKS` (1 : N)
- To prevent race conditions while a customer completes their checkout, a seat is temporarily held in `SEAT_LOCKS`.
- Constraint: `UNIQUE (show_id, seat_id)` prevents two concurrent users from holding a lock on the same seat for the same show.
- Each lock has an expiration timestamp (`expires_at`, 5-minute TTL).
