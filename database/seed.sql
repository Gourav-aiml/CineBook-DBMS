-- CineBook - Movie Ticket Booking System
-- Database Seed Data Script
-- Author: CineBook DBMS Project Team

USE cinebook;

-- -------------------------------------------------------------
-- 1. SEED USERS (Password for all demo users is 'password123')
-- -------------------------------------------------------------
INSERT INTO users (name, email, password_hash) VALUES
('Rahul Sharma', 'rahul@example.com', 'scrypt:32768:8:1$qrMW0hq9UsHowJlY$45585afa80a119a53a850013257e89b4c97692281b4b91b0515a4622a4cfe7acc8bea2540ca821925465578b9bb0f988e92db4e4de25dd4a3480280d39d4635f'),
('Priya Patel', 'priya@example.com', 'scrypt:32768:8:1$qrMW0hq9UsHowJlY$45585afa80a119a53a850013257e89b4c97692281b4b91b0515a4622a4cfe7acc8bea2540ca821925465578b9bb0f988e92db4e4de25dd4a3480280d39d4635f'),
('Gourav Saha', 'gourav@example.com', 'scrypt:32768:8:1$qrMW0hq9UsHowJlY$45585afa80a119a53a850013257e89b4c97692281b4b91b0515a4622a4cfe7acc8bea2540ca821925465578b9bb0f988e92db4e4de25dd4a3480280d39d4635f');

-- -------------------------------------------------------------
-- 2. SEED MOVIES (8 Diverse Movies with realistic details)
-- -------------------------------------------------------------
INSERT INTO movies (title, description, genre, language, duration_minutes, release_date, poster_url) VALUES
('Jawan', 'A high-octane action thriller outlining the emotional journey of a man who is set to rectify the wrongs in the society while fulfilling a promise.', 'Action/Thriller', 'Hindi', 169, '2023-09-07', 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=600&auto=format&fit=crop&q=80'),
('Interstellar', 'When Earth becomes uninhabitable in the future, a farmer and ex-NASA pilot, Joseph Cooper, is tasked to pilot a spacecraft along with a team of researchers to find a new planet for humans.', 'Sci-Fi/Adventure', 'English', 169, '2014-11-07', 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&auto=format&fit=crop&q=80'),
('Kantara', 'When greed paves the way for betrayal, scheming and murder, a young tribal man reluctantly dons the traditions of his ancestors to seek justice.', 'Action/Mystery', 'Kannada', 148, '2022-09-30', 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600&auto=format&fit=crop&q=80'),
('RRR', 'A fictitious story about two legendary revolutionaries and their journey away from home before they began fighting for their country in the 1920s.', 'Action/Drama', 'Telugu', 187, '2022-03-25', 'https://images.unsplash.com/photo-1594909122845-11baa439b7bf?w=600&auto=format&fit=crop&q=80'),
('Oppenheimer', 'The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb during World War II.', 'Biography/Drama', 'English', 180, '2023-07-21', 'https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=600&auto=format&fit=crop&q=80'),
('3 Idiots', 'Two friends are searching for their long lost companion. They revisit their college days and recall the memories of their friend who inspired them to think differently.', 'Comedy/Drama', 'Hindi', 170, '2009-12-25', 'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=600&auto=format&fit=crop&q=80'),
('Dune: Part Two', 'Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family.', 'Sci-Fi/Adventure', 'English', 166, '2024-03-01', 'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=600&auto=format&fit=crop&q=80'),
('Drishyam 2', 'A gripping tale of an investigation and a family threatened by it. Will Vijay Salgaonkar be able to protect his family this time?', 'Thriller/Crime', 'Hindi', 140, '2022-11-18', 'https://images.unsplash.com/photo-1485846234645-a62644f84728?w=600&auto=format&fit=crop&q=80');

-- -------------------------------------------------------------
-- 3. SEED CINEMAS (3 Realistic Cinemas in Kolkata)
-- -------------------------------------------------------------
INSERT INTO cinemas (name, address, city) VALUES
('PVR INOX South City Mall', '375 Prince Anwar Shah Road, Jadavpur', 'Kolkata'),
('Cinepolis Acropolis Mall', '1858 Rajdanga Main Road, Kasba', 'Kolkata'),
('Miraj Cinemas Mani Square', '164/1 Maniktala Main Road, EM Bypass', 'Kolkata');

-- -------------------------------------------------------------
-- 4. SEED SCREENS (2 Screens per Cinema = 6 Screens total)
-- -------------------------------------------------------------
INSERT INTO screens (cinema_id, screen_name, capacity) VALUES
(1, 'Audi 1 (IMAX)', 40),
(1, 'Audi 2 (Dolby Atmos)', 40),
(2, 'Screen 1 (4DX)', 40),
(2, 'Screen 2 (Macro XE)', 40),
(3, 'Screen 1 (Gold Class)', 40),
(3, 'Screen 2 (Silver Screen)', 40);

-- -------------------------------------------------------------
-- 5. SEED SEATS (40 Seats per Screen: Rows A-E, Seats 1-8)
-- Row A, B: REGULAR (8 * 2 = 16)
-- Row C, D: PREMIUM (8 * 2 = 16)
-- Row E: RECLINER (8 * 1 = 8)
-- Total = 40 seats per screen * 6 screens = 240 physical seats
-- -------------------------------------------------------------
INSERT INTO seats (screen_id, row_label, seat_number, seat_type)
SELECT s.screen_id, r.row_label, n.seat_number,
       CASE 
           WHEN r.row_label IN ('A', 'B') THEN 'REGULAR'
           WHEN r.row_label IN ('C', 'D') THEN 'PREMIUM'
           ELSE 'RECLINER'
       END AS seat_type
FROM screens s
CROSS JOIN (
    SELECT 'A' AS row_label UNION ALL
    SELECT 'B' UNION ALL
    SELECT 'C' UNION ALL
    SELECT 'D' UNION ALL
    SELECT 'E'
) r
CROSS JOIN (
    SELECT 1 AS seat_number UNION ALL
    SELECT 2 UNION ALL
    SELECT 3 UNION ALL
    SELECT 4 UNION ALL
    SELECT 5 UNION ALL
    SELECT 6 UNION ALL
    SELECT 7 UNION ALL
    SELECT 8
) n;

-- -------------------------------------------------------------
-- 6. SEED SHOWS (18 Scheduled Shows across screens and dates)
-- Dates dynamically set relative to CURRENT_DATE:
-- CURRENT_DATE, CURRENT_DATE + 1, CURRENT_DATE + 2
-- -------------------------------------------------------------
INSERT INTO shows (movie_id, screen_id, show_date, start_time, end_time, ticket_price) VALUES
-- Today's Shows
(1, 1, CURRENT_DATE, '10:30:00', '13:20:00', 250.00),
(1, 1, CURRENT_DATE, '14:30:00', '17:20:00', 300.00),
(2, 2, CURRENT_DATE, '11:00:00', '13:50:00', 280.00),
(2, 2, CURRENT_DATE, '18:00:00', '20:50:00', 350.00),
(3, 3, CURRENT_DATE, '13:00:00', '15:30:00', 220.00),
(4, 4, CURRENT_DATE, '16:00:00', '19:10:00', 260.00),
(5, 5, CURRENT_DATE, '19:30:00', '22:30:00', 400.00),
(6, 6, CURRENT_DATE, '10:00:00', '12:50:00', 180.00),

-- Tomorrow's Shows (CURRENT_DATE + 1)
(1, 2, DATE_ADD(CURRENT_DATE, INTERVAL 1 DAY), '11:30:00', '14:20:00', 260.00),
(2, 1, DATE_ADD(CURRENT_DATE, INTERVAL 1 DAY), '15:00:00', '17:50:00', 320.00),
(3, 3, DATE_ADD(CURRENT_DATE, INTERVAL 1 DAY), '17:30:00', '20:00:00', 240.00),
(4, 5, DATE_ADD(CURRENT_DATE, INTERVAL 1 DAY), '14:00:00', '17:10:00', 350.00),
(7, 4, DATE_ADD(CURRENT_DATE, INTERVAL 1 DAY), '18:45:00', '21:30:00', 300.00),
(8, 6, DATE_ADD(CURRENT_DATE, INTERVAL 1 DAY), '20:00:00', '22:20:00', 200.00),

-- Day After Tomorrow's Shows (CURRENT_DATE + 2)
(5, 1, DATE_ADD(CURRENT_DATE, INTERVAL 2 DAY), '12:00:00', '15:00:00', 300.00),
(6, 2, DATE_ADD(CURRENT_DATE, INTERVAL 2 DAY), '15:30:00', '18:20:00', 220.00),
(7, 3, DATE_ADD(CURRENT_DATE, INTERVAL 2 DAY), '18:00:00', '20:45:00', 280.00),
(8, 5, DATE_ADD(CURRENT_DATE, INTERVAL 2 DAY), '21:00:00', '23:20:00', 350.00);

-- -------------------------------------------------------------
-- 7. SEED BOOKINGS, BOOKING_SEATS & PAYMENTS
-- Show 1 (Screen 1): Pre-book seats A1, A2 for Rahul
-- Show 1 (Screen 1): Pre-book seats C3, C4 for Priya
-- -------------------------------------------------------------
-- Booking 1: Rahul Sharma books seats A1, A2 for Show 1 (2 tickets * 250 = 500)
INSERT INTO bookings (user_id, show_id, booking_time, status, total_amount) VALUES
(1, 1, DATE_SUB(NOW(), INTERVAL 2 HOUR), 'CONFIRMED', 500.00);

SET @b1_id = LAST_INSERT_ID();

INSERT INTO booking_seats (booking_id, show_id, seat_id)
SELECT @b1_id, 1, seat_id FROM seats 
WHERE screen_id = 1 AND row_label = 'A' AND seat_number IN (1, 2);

INSERT INTO payments (booking_id, amount, payment_status, payment_time) VALUES
(@b1_id, 500.00, 'SUCCESS', DATE_SUB(NOW(), INTERVAL 2 HOUR));

-- Booking 2: Priya Patel books seats C3, C4 for Show 1 (2 tickets * 250 = 500)
INSERT INTO bookings (user_id, show_id, booking_time, status, total_amount) VALUES
(2, 1, DATE_SUB(NOW(), INTERVAL 1 HOUR), 'CONFIRMED', 500.00);

SET @b2_id = LAST_INSERT_ID();

INSERT INTO booking_seats (booking_id, show_id, seat_id)
SELECT @b2_id, 1, seat_id FROM seats 
WHERE screen_id = 1 AND row_label = 'C' AND seat_number IN (3, 4);

INSERT INTO payments (booking_id, amount, payment_status, payment_time) VALUES
(@b2_id, 500.00, 'SUCCESS', DATE_SUB(NOW(), INTERVAL 1 HOUR));
