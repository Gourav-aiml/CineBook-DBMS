# CineBook — Core DBMS Concepts & Theoretical Foundations

This document explains the core Database Management Systems (DBMS) principles implemented and demonstrated in **CineBook**, including ACID properties, transaction lifecycles, concurrency control, and Two-Phase Locking (2PL).

---

## 1. ACID Properties Demonstrated

A database transaction is a logical unit of work that must satisfy the ACID properties:

### 1.1 Atomicity ("All or Nothing")
- **DBMS Concept:** Either all operations within a transaction succeed and are permanently committed, or if any operation fails, the transaction is completely rolled back to its initial state.
- **In CineBook:** The booking confirmation workflow (`/booking/confirm`) executes across four interconnected tables:
  1. `bookings` (header insertion)
  2. `booking_seats` (associative junction entries for every selected seat)
  3. `payments` (transaction settlement)
  4. `seat_locks` (releasing temporary reservations)
- **Failure Scenario:** If a customer attempts to book 3 seats (`A1`, `A2`, `A3`) and `A2` is detected as already booked during insertion, a Python exception is raised, immediately triggering `conn.rollback()`.
- **Proof:** `A1` and `A3` are NOT partially inserted into `booking_seats`. Atomicity ensures zero partial states.

### 1.2 Consistency ("Preserving Invariants")
- **DBMS Concept:** A transaction transforms the database from one valid state to another valid state, satisfying all explicit schema constraints, foreign keys, checks, and application invariants.
- **In CineBook:**
  - Foreign key cascades ensure orphan seat bookings cannot exist without a valid show or user.
  - The schema invariant `UNIQUE KEY uq_show_seat_booked (show_id, seat_id)` guarantees that no two active bookings can point to the same physical seat for the same show.
  - Total booking amount equals `COUNT(booking_seats) * shows.ticket_price`.

### 1.3 Isolation ("Independent Concurrency")
- **DBMS Concept:** Intermediate states of concurrent transactions are hidden from each other until committed.
- **In CineBook:** MySQL's default InnoDB isolation level is **REPEATABLE READ** with Multiversion Concurrency Control (MVCC) and next-key locking. CineBook leverages explicit pessimistic row locking (`SELECT ... FOR UPDATE`) during booking confirmation to serialize competing transactions attempting to book the same show.

### 1.4 Durability ("Persistent Writes")
- **DBMS Concept:** Once a transaction is committed, its modifications survive system crashes or power failures.
- **In CineBook:** InnoDB's write-ahead redo log (`ib_logfile`) guarantees that when `conn.commit()` returns, all seat allocations, payment timestamps, and booking IDs are persisted to disk.

---

## 2. Transaction Lifecycle & Syntax

Every critical modification in CineBook uses explicit MySQL transactions managed via Python context managers:

```sql
-- Step 1: Start Transaction
START TRANSACTION;

-- Step 2: Prune expired reservation locks
DELETE FROM seat_locks WHERE expires_at < NOW();

-- Step 3: Pessimistic Row Locking on Show
SELECT show_id, ticket_price FROM shows WHERE show_id = 1 FOR UPDATE;

-- Step 4: Verify seat availability with row locks
SELECT bs.seat_id 
FROM booking_seats bs 
WHERE bs.show_id = 1 AND bs.seat_id IN (26, 27) 
FOR UPDATE;

-- Step 5: Insert Booking Header
INSERT INTO bookings (user_id, show_id, booking_time, status, total_amount)
VALUES (1, 1, NOW(), 'CONFIRMED', 500.00);

-- Step 6: Insert Relational Seat Allocations
INSERT INTO booking_seats (booking_id, show_id, seat_id) VALUES (LAST_INSERT_ID(), 1, 26);
INSERT INTO booking_seats (booking_id, show_id, seat_id) VALUES (LAST_INSERT_ID(), 1, 27);

-- Step 7: Record Payment
INSERT INTO payments (booking_id, amount, payment_status, payment_time)
VALUES (LAST_INSERT_ID(), 500.00, 'SUCCESS', NOW());

-- Step 8: Release temporary locks
DELETE FROM seat_locks WHERE show_id = 1 AND seat_id IN (26, 27);

-- Step 9: Commit Transaction
COMMIT;
-- (Or ROLLBACK if any error occurs above)
```

---

## 3. Concurrency Control & Two-Phase Locking (2PL)

### 3.1 What is Two-Phase Locking (2PL)?
In DBMS theory, Two-Phase Locking is a concurrency control protocol that guarantees conflict serializability of concurrent transactions. It divides a transaction's execution into two distinct phases:
1. **Growing Phase:** The transaction acquires locks on resources (read/shared locks, write/exclusive locks) as needed. No locks can be released during this phase.
2. **Shrinking Phase:** Once the transaction releases its first lock, it enters the shrinking phase. No new locks can be acquired; only existing locks are released.
- In **Strict 2PL**, all exclusive locks are held until the very end of the transaction (`COMMIT` or `ROLLBACK`) to prevent dirty reads and cascading aborts.

### 3.2 How CineBook Demonstrates 2PL via MySQL InnoDB
> **Important Distinction:** MySQL’s transaction and row-locking mechanisms provide the locking behavior used by the application, while the project demonstrates the DBMS concept of two-phase locking.

In CineBook:
- **Growing Phase in CineBook:** When `/booking/confirm` begins, the transaction executes:
  - `SELECT ... FROM shows WHERE show_id = %s FOR UPDATE` (acquires an exclusive row lock on the show).
  - `SELECT ... FROM booking_seats WHERE ... FOR UPDATE` (acquires exclusive next-key locks on the seat reservation records).
  - During this phase, locks are continuously accumulated.
- **Shrinking Phase in CineBook:** InnoDB adheres to Strict 2PL: when the transaction commits (`conn.commit()`) or rolls back (`conn.rollback()`), all acquired row locks on `shows` and `booking_seats` are simultaneously released, allowing other waiting transactions to proceed.

---

## 4. Multi-Level Double-Booking Prevention Architecture

CineBook implements defense-in-depth to prevent double bookings across 3 architectural layers:

```
[Layer 1: Frontend User Experience]
  └── JavaScript checks seat state, disables booked/locked seats, tracks 5-min timer.
       │ (Note: Frontend validation is purely for UX; cannot prevent concurrent attacks)
       ▼
[Layer 2: Backend Application & Pessimistic Locks]
  └── Flask route acquires SELECT ... FOR UPDATE within a MySQL transaction.
  └── Verifies active 5-minute locks in seat_locks.
  └── Rejects collision with 409 Conflict if locked by another user.
       │
       ▼
[Layer 3: Relational Storage Engine Hard Invariant (MySQL InnoDB)]
  └── UNIQUE KEY uq_show_seat_booked (show_id, seat_id) on table booking_seats.
  └── Physically prevents duplicate insertion at the B-Tree storage engine level.
  └── Triggers Error 1062 (ER_DUP_ENTRY) and forces atomic ROLLBACK.
```
