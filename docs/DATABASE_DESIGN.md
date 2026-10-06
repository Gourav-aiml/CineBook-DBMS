# CineBook — Relational Database Design & Normalization

This document provides a comprehensive technical breakdown of the relational database architecture designed for **CineBook**, including Functional Dependencies, Candidate Keys, and a step-by-step verification of **First Normal Form (1NF)**, **Second Normal Form (2NF)**, and **Third Normal Form (3NF)**.

---

## 1. Functional Dependencies (FDs)

A Functional Dependency \(X \rightarrow Y\) indicates that attribute set \(X\) uniquely determines attribute set \(Y\).

### Table: `users`
- **FD 1.1:** `user_id` \(\rightarrow\) `name`, `email`, `password_hash`, `created_at` *(Primary Key)*
- **FD 1.2:** `email` \(\rightarrow\) `user_id`, `name`, `password_hash`, `created_at` *(Alternate Key / Candidate Key)*

### Table: `movies`
- **FD 2.1:** `movie_id` \(\rightarrow\) `title`, `description`, `genre`, `language`, `duration_minutes`, `release_date`, `poster_url`, `created_at`

### Table: `cinemas`
- **FD 3.1:** `cinema_id` \(\rightarrow\) `name`, `address`, `city`

### Table: `screens`
- **FD 4.1:** `screen_id` \(\rightarrow\) `cinema_id`, `screen_name`, `capacity`
- **FD 4.2:** `{cinema_id, screen_name}` \(\rightarrow\) `screen_id`, `capacity` *(Candidate Key)*

### Table: `seats`
- **FD 5.1:** `seat_id` \(\rightarrow\) `screen_id`, `row_label`, `seat_number`, `seat_type`
- **FD 5.2:** `{screen_id, row_label, seat_number}` \(\rightarrow\) `seat_id`, `seat_type` *(Candidate Key)*

### Table: `shows`
- **FD 6.1:** `show_id` \(\rightarrow\) `movie_id`, `screen_id`, `show_date`, `start_time`, `end_time`, `ticket_price`
- **FD 6.2:** `{screen_id, show_date, start_time}` \(\rightarrow\) `show_id`, `movie_id`, `end_time`, `ticket_price` *(Candidate Key)*

### Table: `bookings`
- **FD 7.1:** `booking_id` \(\rightarrow\) `user_id`, `show_id`, `booking_time`, `status`, `total_amount`

### Table: `booking_seats`
- **FD 8.1:** `{booking_id, seat_id}` \(\rightarrow\) `show_id` *(Composite Primary Key)*
- **FD 8.2:** `{show_id, seat_id}` \(\rightarrow\) `booking_id` *(Candidate Key enforcing 1-to-1 seat allocation per show)*

### Table: `seat_locks`
- **FD 9.1:** `lock_id` \(\rightarrow\) `show_id`, `seat_id`, `user_id`, `locked_at`, `expires_at`
- **FD 9.2:** `{show_id, seat_id}` \(\rightarrow\) `lock_id`, `user_id`, `locked_at`, `expires_at` *(Candidate Key enforcing temporary exclusive lock)*

### Table: `payments`
- **FD 10.1:** `payment_id` \(\rightarrow\) `booking_id`, `amount`, `payment_status`, `payment_time`
- **FD 10.2:** `booking_id` \(\rightarrow\) `payment_id`, `amount`, `payment_status`, `payment_time` *(1:1 relationship with booking)*

---

## 2. Normalization Process

Database normalization systematically eliminates data redundancy, anomalies (insertion, update, deletion), and inconsistent dependencies.

### 2.1 First Normal Form (1NF)
**Requirement:** 
- Every column must hold atomic (indivisible) values.
- There must be no repeating groups or multivalued arrays stored in a single attribute.
- Each record must be uniquely identifiable via a Primary Key.

**CineBook Compliance:**
- **No Comma-Separated Values:** In a naive, non-normalized design, booked seats might be stored as `"A1, A2, A3"` in a single text column inside `bookings`. In CineBook, this multivalued group is completely decomposed into the associative entity table `booking_seats`, where each row represents an atomic tuple `(booking_id, seat_id)`.
- **Atomic Data Fields:** Dates (`show_date`) and times (`start_time`, `end_time`) are stored as native SQL scalar types rather than composite strings.
- **Unique Records:** Every table defines a surrogate Primary Key (`AUTO_INCREMENT`) or composite primary key (`(booking_id, seat_id)`).

---

### 2.2 Second Normal Form (2NF)
**Requirement:**
- The relation must already be in 1NF.
- There must be **no partial functional dependencies**; every non-prime attribute must depend on the **entire candidate key**, not just a subset of a composite key.

**CineBook Compliance:**
- The only table with a composite key is `booking_seats (booking_id, seat_id)`.
- In `booking_seats`, the only other attribute is `show_id` which acts as the relational context linking the booked seat back to the scheduled show to uphold the unique booking constraint.
- Notice that movie information (`title`, `duration`), user information (`user_name`, `email`), and physical seat metadata (`row_label`, `seat_number`, `seat_type`) are **NOT stored redundantly** in `booking_seats`. If they were, `movie_title` would depend on `show_id` (a partial key), violating 2NF.
- Instead, each entity lives in its own dedicated relation, eliminating all partial dependencies.

---

### 2.3 Third Normal Form (3NF)
**Requirement:**
- The relation must already be in 2NF.
- There must be **no transitive dependencies**; every non-prime attribute must depend directly on the primary key, and only on the primary key (\(X \rightarrow Y\) where \(Y \rightarrow Z\) is forbidden if \(Z\) is non-prime).

**CineBook Compliance:**
- **Cinema & Screen Separation:** A screen is in a cinema, and a cinema is in a city. If `screens` contained `cinema_name`, `cinema_address`, and `city`, we would have:
  \[
  \text{screen\_id} \rightarrow \text{cinema\_id} \rightarrow \text{city}
  \]
  This transitive dependency would lead to update anomalies if a cinema's address changes. In CineBook, cinema metadata is isolated into the `cinemas` table. `screens` maintains only a foreign key reference `cinema_id`.
- **Movie & Show Separation:** `shows` stores only showtime scheduling parameters (`show_date`, `start_time`, `ticket_price`). It refers to `movie_id`. If `movie_title` or `director` were in `shows`, `show_id \rightarrow movie_id \rightarrow movie_title` would be a transitive dependency.
- **Seat & Screen Separation:** `seats` stores physical seat positioning relative to `screen_id`. Capacity is retained on `screens`.
- **Payment & Booking Separation:** `payments` isolates transaction state and timestamps from customer booking headers.

Every relation in CineBook is strictly in **Third Normal Form (3NF)** (and satisfies Boyce-Codd Normal Form BCNF for all candidate keys).

---

## 3. Candidate Keys and Invariants

| Table | Primary Key | Candidate / Unique Keys |
| :--- | :--- | :--- |
| `users` | `user_id` | `email` |
| `movies` | `movie_id` | `movie_id` |
| `cinemas` | `cinema_id` | `cinema_id` |
| `screens` | `screen_id` | `{cinema_id, screen_name}` |
| `seats` | `seat_id` | `{screen_id, row_label, seat_number}` |
| `shows` | `show_id` | `{screen_id, show_date, start_time}` |
| `bookings` | `booking_id` | `booking_id` |
| `booking_seats`| `{booking_id, seat_id}` | `{show_id, seat_id}` |
| `seat_locks` | `lock_id` | `{show_id, seat_id}` |
| `payments` | `payment_id` | `booking_id` |

### Critical Invariant: Hard Double-Booking Prevention
The candidate key `UNIQUE (show_id, seat_id)` on `booking_seats` ensures that even if application logic were to attempt simultaneous concurrent writes, MySQL's InnoDB storage engine will reject the second insertion with an `ER_DUP_ENTRY (1062)` error, guaranteeing relational integrity at the storage engine level.
