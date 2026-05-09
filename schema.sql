-- ============================================================
--  EVENT TICKET RESERVATION SYSTEM
--  Author: AWA NADEGE KONE
--  Run this in Railway MySQL → Query tab after adding MySQL plugin
-- ============================================================

CREATE TABLE IF NOT EXISTS customer (
    customer_id  INT           NOT NULL AUTO_INCREMENT,
    full_name    VARCHAR(100)  NOT NULL,
    email        VARCHAR(150)  NOT NULL UNIQUE,
    phone        VARCHAR(20)   DEFAULT NULL,
    address      TEXT          DEFAULT NULL,
    created_at   DATETIME      NOT NULL DEFAULT NOW(),
    PRIMARY KEY (customer_id)
);

CREATE TABLE IF NOT EXISTS venue (
    venue_id        INT          NOT NULL AUTO_INCREMENT,
    name            VARCHAR(150) NOT NULL,
    location        TEXT         NOT NULL,
    total_capacity  INT          NOT NULL,
    PRIMARY KEY (venue_id)
);

CREATE TABLE IF NOT EXISTS event (
    event_id    INT           NOT NULL AUTO_INCREMENT,
    venue_id    INT           NOT NULL,
    event_name  VARCHAR(200)  NOT NULL,
    event_date  DATE          NOT NULL,
    event_time  TIME          NOT NULL,
    description TEXT          DEFAULT NULL,
    status      ENUM('upcoming','ongoing','cancelled','completed') NOT NULL DEFAULT 'upcoming',
    PRIMARY KEY (event_id),
    FOREIGN KEY (venue_id) REFERENCES venue(venue_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS seat (
    seat_id      INT             NOT NULL AUTO_INCREMENT,
    venue_id     INT             NOT NULL,
    seat_number  VARCHAR(10)     NOT NULL,
    row_label    VARCHAR(5)      NOT NULL,
    category     ENUM('VVIP','VIP','Standard') NOT NULL,
    status       ENUM('available','reserved','booked') NOT NULL DEFAULT 'available',
    price        DECIMAL(10,2)   NOT NULL,
    PRIMARY KEY (seat_id),
    FOREIGN KEY (venue_id) REFERENCES venue(venue_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY uq_seat (venue_id, row_label, seat_number)
);

CREATE TABLE IF NOT EXISTS booking (
    booking_id    INT          NOT NULL AUTO_INCREMENT,
    customer_id   INT          NOT NULL,
    event_id      INT          NOT NULL,
    seat_id       INT          NOT NULL,
    booking_ref   VARCHAR(20)  NOT NULL UNIQUE,
    status        ENUM('pending','confirmed','cancelled') NOT NULL DEFAULT 'pending',
    booked_at     DATETIME     NOT NULL DEFAULT NOW(),
    cancelled_at  DATETIME     DEFAULT NULL,
    cancel_reason TEXT         DEFAULT NULL,
    PRIMARY KEY (booking_id),
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (event_id)    REFERENCES event(event_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (seat_id)     REFERENCES seat(seat_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS payment (
    payment_id      INT           NOT NULL AUTO_INCREMENT,
    booking_id      INT           NOT NULL,
    amount          DECIMAL(10,2) NOT NULL,
    payment_method  VARCHAR(50)   NOT NULL,
    status          ENUM('pending','paid','refunded','failed') NOT NULL DEFAULT 'pending',
    paid_at         DATETIME      DEFAULT NULL,
    refunded_at     DATETIME      DEFAULT NULL,
    PRIMARY KEY (payment_id),
    FOREIGN KEY (booking_id) REFERENCES booking(booking_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ── SAMPLE DATA ──────────────────────────────────────────────

INSERT INTO venue (name, location, total_capacity) VALUES
('Grand Arena',          'Warsaw City Centre, Poland',  500),
('Blue Note Hall',       'Krakow Old Town, Poland',     200),
('Tech Hub Auditorium',  'Gdansk Innovation District',  300);

INSERT INTO customer (full_name, email, phone, address) VALUES
('Awa Nadege Kone',   'awa.kone@email.com',   '+48 111 222 333', 'Warsaw, Poland'),
('Jean Dupont',       'jean@email.com',        '+33 600 000 001', 'Paris, France'),
('Amara Diallo',      'amara@email.com',       '+225 070 000 001','Abidjan, Ivory Coast');

INSERT INTO event (venue_id, event_name, event_date, event_time, description, status) VALUES
(1, 'Jazz Night Live 2025',    '2025-08-15', '19:00:00', 'A spectacular jazz evening.', 'upcoming'),
(2, 'Tech Summit Warsaw',      '2025-09-10', '09:00:00', 'Annual technology conference.', 'upcoming'),
(3, 'Classical Orchestra Gala','2025-10-05', '18:30:00', 'An evening of classical music.', 'upcoming');

INSERT INTO seat (venue_id, seat_number, row_label, category, price) VALUES
(1,'01','A','VVIP',800.00),(1,'02','A','VVIP',800.00),(1,'03','A','VVIP',800.00),
(1,'01','B','VVIP',750.00),(1,'02','B','VVIP',750.00),
(1,'01','C','VIP', 300.00),(1,'02','C','VIP', 300.00),
(1,'01','D','VIP', 280.00),(1,'02','D','VIP', 280.00),
(1,'01','E','Standard',80.00),(1,'02','E','Standard',80.00),(1,'03','E','Standard',80.00),
(1,'01','F','Standard',70.00),(1,'02','F','Standard',70.00),
(2,'01','A','VVIP',600.00),(2,'02','A','VVIP',600.00),
(2,'01','B','VIP', 200.00),(2,'02','B','VIP', 200.00),
(2,'01','C','Standard',50.00),(2,'02','C','Standard',50.00);

INSERT INTO booking (customer_id,event_id,seat_id,booking_ref,status,booked_at) VALUES
(1,1,1,'BK-00001','confirmed',NOW()),
(2,2,6,'BK-00002','confirmed',NOW());

UPDATE seat SET status='booked' WHERE seat_id IN (1,6);

INSERT INTO payment (booking_id,amount,payment_method,status,paid_at) VALUES
(1,800.00,'card','paid',NOW()),
(2,300.00,'mobile_money','paid',NOW());
