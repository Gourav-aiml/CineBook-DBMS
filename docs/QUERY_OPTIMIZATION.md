# CineBook — Query Optimization & Execution Plan Analysis

This document demonstrates the practical SQL query optimization techniques used across the **CineBook** application, grounded in verified MySQL 8 execution plans (`EXPLAIN`).

---

## 1. Key Query Optimization Principles Applied

### 1.1 Selecting Required Columns Over `SELECT *`
- **Issue:** Using `SELECT *` forces MySQL to fetch all columns from the clustered index, including large `TEXT` or `VARCHAR(500)` columns (like `movies.description` or `poster_url`), which increases network I/O and cache memory pressure.
- **Optimization:** In show listings and seat selection routes, we explicitly select only the columns needed by the user interface:
  ```sql
  -- Optimized: Only fetches 4 lightweight columns
  SELECT s.show_id, s.start_time, s.ticket_price, sc.screen_name
  FROM shows s
  JOIN screens sc ON s.screen_id = sc.screen_id
  WHERE s.movie_id = %s;
  ```

### 1.2 Filtering Before Joining (Pushdown Predicates)
- By applying `WHERE s.movie_id = 1 AND s.show_date = CURRENT_DATE` directly to the leading table in the join, MySQL eliminates non-matching rows before attempting lookups into `screens` and `cinemas`.

### 1.3 Covering Indexes to Eliminate Clustered Table Lookups
- In the real-time seat availability query, joining `booking_seats bs ON bs.show_id = sh.show_id AND bs.seat_id = st.seat_id` uses the unique composite index `uq_show_seat_booked(show_id, seat_id)`.
- Because all requested columns (`show_id`, `seat_id`) reside directly inside the index leaf node, MySQL reads the index directly (`Extra: Using index`) without dereferencing table data blocks.

---

## 2. Real Execution Plan Analysis (`EXPLAIN`)

### Case Study 1: Real-Time Dynamic Seat Availability Map
This is the most critical query in the application, called every time a user inspects auditorium seats.

#### Query:
```sql
EXPLAIN SELECT 
    st.seat_id, st.row_label, st.seat_number, st.seat_type,
    CASE 
        WHEN bs.seat_id IS NOT NULL THEN 'BOOKED'
        WHEN sl.seat_id IS NOT NULL AND sl.expires_at > NOW() THEN 'LOCKED'
        ELSE 'AVAILABLE'
    END AS status
FROM seats st
JOIN shows sh ON sh.show_id = 1 AND st.screen_id = sh.screen_id
LEFT JOIN booking_seats bs ON bs.show_id = sh.show_id AND bs.seat_id = st.seat_id
LEFT JOIN seat_locks sl ON sl.show_id = sh.show_id AND sl.seat_id = st.seat_id AND sl.expires_at > NOW()
ORDER BY st.row_label, st.seat_number;
```

#### Actual MySQL 8 Output:
```
+----+-------------+-------+------------+--------+-------------------------------------------------------+----------------------+---------+---------------------------+------+----------+-------------+
| id | select_type | table | partitions | type   | possible_keys                                         | key                  | key_len | ref                       | rows | filtered | Extra       |
+----+-------------+-------+------------+--------+-------------------------------------------------------+----------------------+---------+---------------------------+------+----------+-------------+
|  1 | SIMPLE      | sh    | NULL       | const  | PRIMARY,uq_screen_showtime,idx_shows_screen           | PRIMARY              | 4       | const                     |    1 |   100.00 | NULL        |
|  1 | SIMPLE      | st    | NULL       | ref    | uq_screen_row_number                                  | uq_screen_row_number | 4       | const                     |   40 |   100.00 | NULL        |
|  1 | SIMPLE      | bs    | NULL       | eq_ref | uq_show_seat_booked,fk_bseats_seat,idx_bseats_show    | uq_show_seat_booked  | 8       | const,cinebook.st.seat_id |    1 |   100.00 | Using index |
|  1 | SIMPLE      | sl    | NULL       | eq_ref | uq_show_seat_locked,fk_locks_seat,idx_locks_expires   | uq_show_seat_locked  | 8       | const,cinebook.st.seat_id |    1 |   100.00 | Using where |
+----+-------------+-------+------------+--------+-------------------------------------------------------+----------------------+---------+---------------------------+------+----------+-------------+
```

#### Plan Interpretation:
1. **`sh` (`shows`):** `type: const`. MySQL recognizes `sh.show_id = 1` as a primary key lookup. The optimizer resolves the row in a single access step.
2. **`st` (`seats`):** `type: ref` using `uq_screen_row_number`. It immediately isolates exactly the 40 seats corresponding to screen 1 without scanning the remaining 200 seats in other auditoriums.
3. **`bs` (`booking_seats`):** `type: eq_ref` using `uq_show_seat_booked`. `eq_ref` is the most efficient join type possible in MySQL. Crucially, `Extra: Using index` confirms that the check is served 100% from RAM cache memory via the B-Tree index without accessing disk table blocks.
4. **`sl` (`seat_locks`):** `type: eq_ref` using `uq_show_seat_locked`. Each seat is tested in \(O(1)\) against any active lock.

---

### Case Study 2: Upcoming Shows by Movie and Date

#### Query:
```sql
EXPLAIN SELECT s.show_id, s.start_time, s.ticket_price, sc.screen_name, c.name AS cinema_name
FROM shows s
JOIN screens sc ON s.screen_id = sc.screen_id
JOIN cinemas c ON sc.cinema_id = c.cinema_id
WHERE s.movie_id = 1 AND s.show_date = CURRENT_DATE;
```

#### Actual MySQL 8 Output:
```
+----+-------------+-------+------------+--------+---------------------------------------------------------+----------------------+---------+-----------------------+------+----------+-------+
| id | select_type | table | partitions | type   | possible_keys                                           | key                  | key_len | ref                   | rows | filtered | Extra |
+----+-------------+-------+------------+--------+---------------------------------------------------------+----------------------+---------+-----------------------+------+----------+-------+
|  1 | SIMPLE      | s     | NULL       | ref    | uq_screen_showtime,idx_shows_movie_date,idx_shows_screen| idx_shows_movie_date | 7       | const,const           |    2 |   100.00 | NULL  |
|  1 | SIMPLE      | sc    | NULL       | eq_ref | PRIMARY,uq_cinema_screen                                | PRIMARY              | 4       | cinebook.s.screen_id  |    1 |   100.00 | NULL  |
|  1 | SIMPLE      | c     | NULL       | eq_ref | PRIMARY                                                 | PRIMARY              | 4       | cinebook.sc.cinema_id |    1 |   100.00 | NULL  |
+----+-------------+-------+------------+--------+---------------------------------------------------------+----------------------+---------+-----------------------+------+----------+-------+
```

#### Plan Interpretation:
- Table `s` uses the composite index `idx_shows_movie_date(movie_id, show_date)`. The optimizer inspects exactly 2 qualifying show rows (`rows: 2`).
- Joined tables `sc` and `c` are accessed via their primary keys (`type: eq_ref`, `rows: 1`).
- The entire join pipeline executes in \(O(1)\) time complexity with zero table scans.
