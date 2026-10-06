-- CineBook — Important SQL Queries
-- Demonstrating Relational Joins, Aggregations, Grouping, and Filtering
-- Used for DBMS Project Demonstration & Viva Examination

USE cinebook;

-- ============================================================================
-- 1. INNER JOIN: List Movies with Scheduled Shows and Ticket Prices
-- ============================================================================
SELECT 
    m.movie_id,
    m.title AS movie_title,
    m.language,
    m.duration_minutes,
    s.show_id,
    s.show_date,
    s.start_time,
    s.ticket_price
FROM movies m
INNER JOIN shows s ON m.movie_id = s.movie_id
WHERE s.show_date >= CURRENT_DATE
ORDER BY s.show_date ASC, s.start_time ASC;


-- ============================================================================
-- 2. MULTI-TABLE JOIN (3 Tables): Show Schedule with Screen and Cinema Details
-- ============================================================================
SELECT 
    sh.show_id,
    m.title AS movie_title,
    c.name AS cinema_name,
    c.city,
    sc.screen_name,
    sh.show_date,
    sh.start_time,
    sh.ticket_price
FROM shows sh
INNER JOIN movies m ON sh.movie_id = m.movie_id
INNER JOIN screens sc ON sh.screen_id = sc.screen_id
INNER JOIN cinemas c ON sc.cinema_id = c.cinema_id
WHERE c.city = 'Kolkata'
ORDER BY sh.show_date, sh.start_time;


-- ============================================================================
-- 3. INNER JOIN: User Bookings with Status and Total Amount
-- ============================================================================
SELECT 
    b.booking_id,
    u.user_id,
    u.name AS user_name,
    u.email,
    b.booking_time,
    b.status AS booking_status,
    b.total_amount
FROM bookings b
INNER JOIN users u ON b.user_id = u.user_id
ORDER BY b.booking_time DESC;


-- ============================================================================
-- 4. MULTI-TABLE JOIN (4 Tables): Detailed Booking Information
-- ============================================================================
SELECT 
    b.booking_id,
    u.name AS customer_name,
    m.title AS movie_title,
    c.name AS cinema_name,
    sc.screen_name,
    sh.show_date,
    sh.start_time,
    b.total_amount,
    b.status
FROM bookings b
INNER JOIN users u ON b.user_id = u.user_id
INNER JOIN shows sh ON b.show_id = sh.show_id
INNER JOIN movies m ON sh.movie_id = m.movie_id
INNER JOIN screens sc ON sh.screen_id = sc.screen_id
INNER JOIN cinemas c ON sc.cinema_id = c.cinema_id
WHERE b.status = 'CONFIRMED'
ORDER BY b.booking_time DESC;


-- ============================================================================
-- 5. COMPLETE SEAT SELECTION & AVAILABILITY QUERY (Crucial for Seat Map)
-- Demonstrates LEFT JOIN with booking_seats and seat_locks
-- Dynamically derives seat status: BOOKED, LOCKED, or AVAILABLE
-- ============================================================================
SELECT 
    st.seat_id,
    st.row_label,
    st.seat_number,
    st.seat_type,
    CASE 
        WHEN bs.seat_id IS NOT NULL THEN 'BOOKED'
        WHEN sl.seat_id IS NOT NULL AND sl.expires_at > NOW() THEN 'LOCKED'
        ELSE 'AVAILABLE'
    END AS seat_status,
    sl.user_id AS locked_by_user_id
FROM seats st
JOIN shows sh ON sh.show_id = 1 AND st.screen_id = sh.screen_id
LEFT JOIN booking_seats bs ON bs.show_id = sh.show_id AND bs.seat_id = st.seat_id
LEFT JOIN seat_locks sl ON sl.show_id = sh.show_id AND sl.seat_id = st.seat_id AND sl.expires_at > NOW()
ORDER BY st.row_label ASC, st.seat_number ASC;


-- ============================================================================
-- 6. AGGREGATION & GROUP BY: Revenue and Ticket Sales per Cinema
-- ============================================================================
SELECT 
    c.name AS cinema_name,
    COUNT(DISTINCT b.booking_id) AS total_bookings,
    COUNT(bs.seat_id) AS total_tickets_sold,
    COALESCE(SUM(b.total_amount), 0.00) AS total_revenue
FROM cinemas c
INNER JOIN screens sc ON c.cinema_id = sc.cinema_id
INNER JOIN shows sh ON sc.screen_id = sh.screen_id
INNER JOIN bookings b ON sh.show_id = b.show_id AND b.status = 'CONFIRMED'
INNER JOIN booking_seats bs ON b.booking_id = bs.booking_id
GROUP BY c.cinema_id, c.name
ORDER BY total_revenue DESC;


-- ============================================================================
-- 7. GROUP BY with HAVING: Movies with more than 1 Scheduled Show
-- ============================================================================
SELECT 
    m.title AS movie_title,
    m.language,
    COUNT(sh.show_id) AS scheduled_show_count,
    MIN(sh.ticket_price) AS lowest_price,
    MAX(sh.ticket_price) AS highest_price
FROM movies m
INNER JOIN shows sh ON m.movie_id = sh.movie_id
GROUP BY m.movie_id, m.title, m.language
HAVING COUNT(sh.show_id) > 1
ORDER BY scheduled_show_count DESC;


-- ============================================================================
-- 8. BOOKING RECEIPT WITH COMPILED SEATS (GROUP_CONCAT)
-- Concatenates seat row and numbers into a clean ticket list (e.g., 'A1, A2')
-- ============================================================================
SELECT 
    b.booking_id,
    u.name AS booked_by,
    m.title AS movie_title,
    c.name AS cinema_name,
    sc.screen_name,
    sh.show_date,
    sh.start_time,
    GROUP_CONCAT(CONCAT(st.row_label, st.seat_number) ORDER BY st.row_label, st.seat_number SEPARATOR ', ') AS seats_booked,
    COUNT(bs.seat_id) AS ticket_count,
    b.total_amount,
    p.payment_status
FROM bookings b
INNER JOIN users u ON b.user_id = u.user_id
INNER JOIN shows sh ON b.show_id = sh.show_id
INNER JOIN movies m ON sh.movie_id = m.movie_id
INNER JOIN screens sc ON sh.screen_id = sc.screen_id
INNER JOIN cinemas c ON sc.cinema_id = c.cinema_id
INNER JOIN booking_seats bs ON b.booking_id = bs.booking_id
INNER JOIN seats st ON bs.seat_id = st.seat_id
LEFT JOIN payments p ON b.booking_id = p.booking_id
WHERE b.booking_id = 1
GROUP BY b.booking_id, u.name, m.title, c.name, sc.screen_name, sh.show_date, sh.start_time, b.total_amount, p.payment_status;
