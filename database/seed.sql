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
-- 2. SEED MOVIES (8 Movies)
-- Movie IDs are kept fixed because shows/bookings reference them.
-- -------------------------------------------------------------
INSERT INTO movies
(movie_id, title, description, genre, language, duration_minutes, release_date, poster_url)
VALUES
(1,
 'The Odyssey',
 'A mythic epic adventure based on the legendary journey of Odysseus returning home after the Trojan War.',
 'Epic/Adventure',
 'English',
 150,
 '2026-07-17',
 '/static/images/the_odyssey.jpg'),

(2,
 'Avengers: Endgame Encore',
 'The Avengers unite once again in an extended cinematic presentation of the legendary battle against Thanos.',
 'Action/Sci-Fi',
 'English',
 181,
 '2026-01-01',
 '/static/images/avengers_endgame.jpg'),

(3,
 'Avengers: Doomsday',
 'The Avengers and their allies face a new catastrophic threat that could change the fate of the universe.',
 'Action/Sci-Fi',
 'English',
 150,
 '2026-12-18',
 '/static/images/avengers_doomsday.jpg'),

(4,
 'M.S. Dhoni: The Untold Story',
 'The inspiring journey of Indian cricket legend Mahendra Singh Dhoni from his early life to international cricket.',
 'Biography/Sports',
 'Hindi',
 184,
 '2016-09-30',
 '/static/images/ms_dhoni.jpg'),

(5,
 'Oppenheimer',
 'The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb during World War II.',
 'Biography/Drama',
 'English',
 180,
 '2023-07-21',
 '/static/images/oppenheimer.jpg'),

(6,
 '3 Idiots',
 'Two friends search for their long-lost companion while remembering their college days and the friend who inspired them to think differently.',
 'Comedy/Drama',
 'Hindi',
 170,
 '2009-12-25',
 '/static/images/3_idiots.jpg'),

(7,
 'Project Hail Mary',
 'A lone astronaut awakens aboard a spacecraft on a mission that could determine the survival of humanity.',
 'Sci-Fi/Adventure',
 'English',
 150,
 '2026-03-20',
 '/static/images/project_hail_mary.jpg'),

(8,
 'Spider-Man: Brand New Day',
 'Spider-Man faces a new chapter and new challenges while protecting New York City.',
 'Action/Superhero',
 'English',
 135,
 '2026-07-31',
 '/static/images/spiderman_brand_new_day.jpg');
 
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
