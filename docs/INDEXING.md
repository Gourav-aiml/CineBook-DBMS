# CineBook — Database Indexing Strategy & Performance Analysis

This document details the indexing architecture designed for **CineBook**, examining how B-Tree indexes accelerate queries, the role of clustered vs secondary indexes, and the trade-offs between read speed and write overhead.

---

## 1. Indexing Fundamentals

An index in a relational database is an auxiliary data structure (typically a balanced B+Tree) that enables the storage engine to locate rows in \(O(\log N)\) time instead of performing a sequential full table scan (\(O(N)\)).

### 1.1 Clustered Index (Primary Key)
In MySQL InnoDB, every table possesses exactly one **Clustered Index**, which is built on the table's Primary Key.
- In `users`, `movies`, `shows`, `bookings`, the table rows themselves are physically organized and stored in the leaf pages of the Primary Key B+Tree.
- Lookups by `PRIMARY KEY` (e.g., `WHERE booking_id = 42`) require zero secondary index traversal and achieve maximum throughput.

### 1.2 Secondary Indexes (Non-Clustered)
Secondary indexes store the indexed column values along with a pointer to the clustered index Primary Key. When querying through a secondary index:
1. InnoDB traverses the secondary B+Tree to find the matching key and associated Primary Key.
2. If additional non-indexed columns are requested, InnoDB performs an index lookup back to the clustered index (a "bookmark lookup" or table dereference).

---

## 2. CineBook Index Catalog & Technical Justification

Below is the complete list of indexes implemented in `database/schema.sql` and the rationale for each:

### 2.1 `users.email`
```sql
CREATE UNIQUE INDEX idx_users_email ON users(email);
```
- **Type:** Unique B-Tree Secondary Index.
- **Query Path:** Authentication login lookups: `SELECT user_id, password_hash FROM users WHERE email = %s`.
- **Justification:** Without this index, every user login or duplicate email registration check would scan the entire `users` table. The index allows \(O(\log N)\) point lookup and enforces uniqueness.

### 2.2 `shows (movie_id, show_date)`
```sql
CREATE INDEX idx_shows_movie_date ON shows(movie_id, show_date);
```
- **Type:** Composite (Multi-Column) Index.
- **Query Path:** Movie details page listing upcoming showtimes: `SELECT ... FROM shows WHERE movie_id = %s AND show_date >= CURRENT_DATE`.
- **Justification:** Leftmost Prefix Rule applies: this index accelerates queries filtering on `movie_id` alone, as well as queries filtering on `movie_id` and sorted or ranged by `show_date`.

### 2.3 `shows.screen_id`
```sql
CREATE INDEX idx_shows_screen ON shows(screen_id);
```
- **Type:** Single-column Foreign Key Index.
- **Query Path:** Joins between `screens` and `shows`, as well as foreign key constraint checks upon show insertion/deletion.

### 2.4 `bookings.user_id`
```sql
CREATE INDEX idx_bookings_user ON bookings(user_id);
```
- **Type:** Single-column Secondary Index.
- **Query Path:** Customer booking history page (`/bookings`): `SELECT ... FROM bookings WHERE user_id = %s ORDER BY booking_time DESC`.
- **Justification:** Enables instant filtering of a user's reservations without inspecting millions of historical bookings from other customers.

### 2.5 `booking_seats (show_id, seat_id)`
```sql
CREATE UNIQUE INDEX uq_show_seat_booked ON booking_seats(show_id, seat_id);
```
- **Type:** Unique Composite Index.
- **Query Path:** Real-time seat availability map and double-booking checks: `SELECT seat_id FROM booking_seats WHERE show_id = %s AND seat_id IN (...)`.
- **Justification:** Serves dual purpose: provides \(O(1)\) duplicate detection for the critical DBMS anti-double-booking invariant and acts as a covering index for availability queries.

### 2.6 `seat_locks (show_id, expires_at)`
```sql
CREATE INDEX idx_seat_locks_show_expires ON seat_locks(show_id, expires_at);
```
- **Type:** Composite Secondary Index.
- **Query Path:** Real-time availability calculation and background lock pruning: `SELECT ... FROM seat_locks WHERE show_id = %s AND expires_at > NOW()`.
- **Justification:** Drastically reduces lock contention and query latency by locating non-expired locks directly in the index leaf pages.

---

## 3. The Indexing Trade-Off: Read vs. Write

While indexes significantly optimize read operations, they introduce deliberate overheads:

| Metric | Non-Indexed Table | Indexed Table |
| :--- | :--- | :--- |
| **SELECT Query Speed** | Slow (\(O(N)\) full table scan) | Fast (\(O(\log N)\) B-Tree traversal) |
| **INSERT Latency** | Very fast (appends row to heap/page) | Slower (must update clustered index + all secondary index B-Trees) |
| **UPDATE Latency** | Fast (updates in-place) | Slower if indexed columns are modified |
| **DELETE Latency** | Fast | Slower (must remove leaf pointers across all B-Trees) |
| **Storage Footprint** | Baseline table data only | +20% to 50% additional disk storage for index pages |

**Conclusion for CineBook:** Because movie ticket booking is a read-heavy system (users browse movies and check seat availability thousands of times before completing one booking), adding these selective indexes yields massive performance gains while keeping write overhead bounded.
