-- CineBook - Movie Ticket Booking System
-- Database Schema Definition (MySQL 8.0+)
-- Author: CineBook DBMS Project Team

DROP DATABASE IF EXISTS cinebook;
CREATE DATABASE cinebook CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cinebook;

-- 1. users Table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. movies Table
CREATE TABLE movies (
    movie_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    genre VARCHAR(50) NOT NULL,
    language VARCHAR(50) NOT NULL,
    duration_minutes INT NOT NULL,
    release_date DATE NOT NULL,
    poster_url VARCHAR(500) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. cinemas Table
CREATE TABLE cinemas (
    cinema_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(50) NOT NULL
) ENGINE=InnoDB;

-- 4. screens Table
CREATE TABLE screens (
    screen_id INT AUTO_INCREMENT PRIMARY KEY,
    cinema_id INT NOT NULL,
    screen_name VARCHAR(50) NOT NULL,
    capacity INT NOT NULL,
    CONSTRAINT fk_screens_cinema FOREIGN KEY (cinema_id) 
        REFERENCES cinemas(cinema_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_cinema_screen UNIQUE (cinema_id, screen_name)
) ENGINE=InnoDB;

-- 5. seats Table
CREATE TABLE seats (
    seat_id INT AUTO_INCREMENT PRIMARY KEY,
    screen_id INT NOT NULL,
    row_label VARCHAR(5) NOT NULL,
    seat_number INT NOT NULL,
    seat_type ENUM('REGULAR', 'PREMIUM', 'RECLINER') NOT NULL DEFAULT 'REGULAR',
    CONSTRAINT fk_seats_screen FOREIGN KEY (screen_id) 
        REFERENCES screens(screen_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_screen_row_number UNIQUE (screen_id, row_label, seat_number)
) ENGINE=InnoDB;

-- 6. shows Table
CREATE TABLE shows (
    show_id INT AUTO_INCREMENT PRIMARY KEY,
    movie_id INT NOT NULL,
    screen_id INT NOT NULL,
    show_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    ticket_price DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_shows_movie FOREIGN KEY (movie_id) 
        REFERENCES movies(movie_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_shows_screen FOREIGN KEY (screen_id) 
        REFERENCES screens(screen_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_screen_showtime UNIQUE (screen_id, show_date, start_time)
) ENGINE=InnoDB;

-- 7. bookings Table
CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    show_id INT NOT NULL,
    booking_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status ENUM('CONFIRMED', 'CANCELLED', 'EXPIRED') NOT NULL DEFAULT 'CONFIRMED',
    total_amount DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_bookings_user FOREIGN KEY (user_id) 
        REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_bookings_show FOREIGN KEY (show_id) 
        REFERENCES shows(show_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 8. booking_seats Table (Many-to-Many between Bookings and Seats)
-- Hard database constraint: A seat cannot be confirmed more than once for the same show.
CREATE TABLE booking_seats (
    booking_id INT NOT NULL,
    show_id INT NOT NULL,
    seat_id INT NOT NULL,
    PRIMARY KEY (booking_id, seat_id),
    CONSTRAINT fk_bseats_booking FOREIGN KEY (booking_id) 
        REFERENCES bookings(booking_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_bseats_show FOREIGN KEY (show_id) 
        REFERENCES shows(show_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_bseats_seat FOREIGN KEY (seat_id) 
        REFERENCES seats(seat_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_show_seat_booked UNIQUE (show_id, seat_id)
) ENGINE=InnoDB;

-- 9. seat_locks Table (Temporary Seat Reservations)
CREATE TABLE seat_locks (
    lock_id INT AUTO_INCREMENT PRIMARY KEY,
    show_id INT NOT NULL,
    seat_id INT NOT NULL,
    user_id INT NOT NULL,
    locked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    CONSTRAINT fk_locks_show FOREIGN KEY (show_id) 
        REFERENCES shows(show_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_locks_seat FOREIGN KEY (seat_id) 
        REFERENCES seats(seat_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_locks_user FOREIGN KEY (user_id) 
        REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_show_seat_locked UNIQUE (show_id, seat_id)
) ENGINE=InnoDB;

-- 10. payments Table (Simulated payment transaction record)
CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_status ENUM('SUCCESS', 'FAILED', 'PENDING') NOT NULL DEFAULT 'SUCCESS',
    payment_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_payments_booking FOREIGN KEY (booking_id) 
        REFERENCES bookings(booking_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- INDEXES FOR QUERY OPTIMIZATION
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_shows_movie_date ON shows(movie_id, show_date);
CREATE INDEX idx_shows_screen ON shows(screen_id);
CREATE INDEX idx_bookings_user ON bookings(user_id);
CREATE INDEX idx_bookings_show ON bookings(show_id);
CREATE INDEX idx_booking_seats_show ON booking_seats(show_id);
CREATE INDEX idx_seat_locks_show_expires ON seat_locks(show_id, expires_at);
