"""
Event Ticket Reservation System — Flask Backend
Author: AWA NADEGE KONE
Deployed on: Railway.app
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import random
import string
import os

app = Flask(__name__)
CORS(app)

# ─── Database connection (Railway injects these automatically) ───
def get_db():
    return mysql.connector.connect(
        host     = os.environ.get("MYSQLHOST",     "localhost"),
        user     = os.environ.get("MYSQLUSER",     "root"),
        password = os.environ.get("MYSQLPASSWORD", ""),
        database = os.environ.get("MYSQLDATABASE", "ticket_reservation_db"),
        port     = int(os.environ.get("MYSQLPORT", 3306))
    )

def generate_booking_ref():
    return "BK-" + "".join(random.choices(string.digits, k=5))

def ok(data=None, message="Success", code=200):
    return jsonify({"status": "success", "message": message, "data": data}), code

def err(message, code=400):
    return jsonify({"status": "error", "message": message}), code


# ════════════════════════════════════════════
#  ROOT — health check
# ════════════════════════════════════════════
@app.route("/")
def home():
    return jsonify({
        "system": "Event Ticket Reservation System",
        "author": "AWA NADEGE KONE",
        "status": "live",
        "endpoints": [
            "GET  /events",
            "GET  /events/<id>/seats/available",
            "GET  /customers",
            "POST /customers",
            "POST /bookings",
            "POST /bookings/<id>/confirm",
            "POST /bookings/<id>/cancel",
            "GET  /bookings/<booking_ref>",
            "GET  /customers/<id>/bookings",
            "GET  /stats"
        ]
    })


# ════════════════════════════════════════════
#  CUSTOMERS
# ════════════════════════════════════════════
@app.route("/customers", methods=["GET"])
def get_all_customers():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM customer ORDER BY created_at DESC")
    rows = cur.fetchall(); cur.close(); db.close()
    return ok(rows)

@app.route("/customers/<int:cid>", methods=["GET"])
def get_customer(cid):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM customer WHERE customer_id=%s", (cid,))
    row = cur.fetchone(); cur.close(); db.close()
    return ok(row) if row else err("Customer not found", 404)

@app.route("/customers", methods=["POST"])
def create_customer():
    data = request.get_json()
    if not data.get("full_name") or not data.get("email"):
        return err("full_name and email are required")
    db = get_db(); cur = db.cursor()
    try:
        cur.execute(
            "INSERT INTO customer (full_name,email,phone,address) VALUES (%s,%s,%s,%s)",
            (data["full_name"], data["email"], data.get("phone"), data.get("address"))
        )
        db.commit()
        cid = cur.lastrowid; cur.close(); db.close()
        return ok({"customer_id": cid}, "Customer created", 201)
    except Exception as e:
        db.rollback(); cur.close(); db.close()
        return err("Email already exists" if "Duplicate" in str(e) else str(e), 409)

@app.route("/customers/<int:cid>", methods=["PUT"])
def update_customer(cid):
    data = request.get_json()
    db = get_db(); cur = db.cursor()
    cur.execute("UPDATE customer SET full_name=%s,phone=%s,address=%s WHERE customer_id=%s",
                (data.get("full_name"), data.get("phone"), data.get("address"), cid))
    db.commit(); cur.close(); db.close()
    return ok(message="Customer updated")

@app.route("/customers/<int:cid>", methods=["DELETE"])
def delete_customer(cid):
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM customer WHERE customer_id=%s", (cid,))
    db.commit(); cur.close(); db.close()
    return ok(message="Customer deleted")

@app.route("/customers/<int:cid>/bookings", methods=["GET"])
def get_customer_bookings(cid):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT b.booking_ref, b.status, b.booked_at,
               e.event_name, e.event_date, e.event_time,
               v.name AS venue_name,
               s.row_label, s.seat_number, s.category, s.price,
               p.status AS payment_status
        FROM booking b
        JOIN event e   ON b.event_id=e.event_id
        JOIN venue v   ON e.venue_id=v.venue_id
        JOIN seat s    ON b.seat_id=s.seat_id
        LEFT JOIN payment p ON p.booking_id=b.booking_id
        WHERE b.customer_id=%s ORDER BY b.booked_at DESC
    """, (cid,))
    rows = cur.fetchall(); cur.close(); db.close()
    return ok(rows)


# ════════════════════════════════════════════
#  VENUES
# ════════════════════════════════════════════
@app.route("/venues", methods=["GET"])
def get_venues():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM venue ORDER BY name")
    rows = cur.fetchall(); cur.close(); db.close()
    return ok(rows)

@app.route("/venues", methods=["POST"])
def create_venue():
    data = request.get_json()
    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO venue (name,location,total_capacity) VALUES (%s,%s,%s)",
                (data["name"], data["location"], data["total_capacity"]))
    db.commit()
    vid = cur.lastrowid; cur.close(); db.close()
    return ok({"venue_id": vid}, "Venue created", 201)


# ════════════════════════════════════════════
#  EVENTS
# ════════════════════════════════════════════
@app.route("/events", methods=["GET"])
def get_events():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT e.*, v.name AS venue_name, v.location, v.total_capacity
        FROM event e JOIN venue v ON e.venue_id=v.venue_id
        WHERE e.event_date >= CURDATE() AND e.status='upcoming'
        ORDER BY e.event_date
    """)
    rows = cur.fetchall(); cur.close(); db.close()
    return ok(rows)

@app.route("/events/all", methods=["GET"])
def get_all_events():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT e.*, v.name AS venue_name, v.location
        FROM event e JOIN venue v ON e.venue_id=v.venue_id
        ORDER BY e.event_date DESC
    """)
    rows = cur.fetchall(); cur.close(); db.close()
    return ok(rows)

@app.route("/events/<int:eid>", methods=["GET"])
def get_event(eid):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT e.*, v.name AS venue_name, v.location, v.total_capacity
        FROM event e JOIN venue v ON e.venue_id=v.venue_id
        WHERE e.event_id=%s
    """, (eid,))
    row = cur.fetchone(); cur.close(); db.close()
    return ok(row) if row else err("Event not found", 404)

@app.route("/events", methods=["POST"])
def create_event():
    data = request.get_json()
    db = get_db(); cur = db.cursor()
    cur.execute("""
        INSERT INTO event (venue_id,event_name,event_date,event_time,description,status)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (data["venue_id"], data["event_name"], data["event_date"],
          data["event_time"], data.get("description"), data.get("status","upcoming")))
    db.commit()
    eid = cur.lastrowid; cur.close(); db.close()
    return ok({"event_id": eid}, "Event created", 201)


# ════════════════════════════════════════════
#  SEATS
# ════════════════════════════════════════════
@app.route("/events/<int:eid>/seats", methods=["GET"])
def get_seats(eid):
    category = request.args.get("category")
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT venue_id FROM event WHERE event_id=%s", (eid,))
    event = cur.fetchone()
    if not event:
        cur.close(); db.close(); return err("Event not found", 404)
    q = "SELECT * FROM seat WHERE venue_id=%s"
    p = [event["venue_id"]]
    if category:
        q += " AND category=%s"; p.append(category)
    q += " ORDER BY category, row_label, seat_number"
    cur.execute(q, p)
    rows = cur.fetchall(); cur.close(); db.close()
    return ok(rows)

@app.route("/events/<int:eid>/seats/available", methods=["GET"])
def get_available_seats(eid):
    category = request.args.get("category")
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT venue_id FROM event WHERE event_id=%s", (eid,))
    event = cur.fetchone()
    if not event:
        cur.close(); db.close(); return err("Event not found", 404)
    q = "SELECT * FROM seat WHERE venue_id=%s AND status='available'"
    p = [event["venue_id"]]
    if category:
        q += " AND category=%s"; p.append(category)
    q += " ORDER BY category, row_label, seat_number"
    cur.execute(q, p)
    rows = cur.fetchall(); cur.close(); db.close()
    return ok(rows)

@app.route("/venues/<int:vid>/seats", methods=["POST"])
def add_seat(vid):
    data = request.get_json()
    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO seat (venue_id,seat_number,row_label,category,price) VALUES (%s,%s,%s,%s,%s)",
                (vid, data["seat_number"], data["row_label"], data["category"], data["price"]))
    db.commit()
    sid = cur.lastrowid; cur.close(); db.close()
    return ok({"seat_id": sid}, "Seat added", 201)


# ════════════════════════════════════════════
#  BOOKINGS
# ════════════════════════════════════════════
@app.route("/bookings", methods=["POST"])
def create_booking():
    data = request.get_json()
    for f in ["customer_id","event_id","seat_id","payment_method"]:
        if not data.get(f):
            return err(f"'{f}' is required")

    db = get_db(); cur = db.cursor(dictionary=True)

    # Check event is upcoming
    cur.execute("SELECT * FROM event WHERE event_id=%s AND status='upcoming' AND event_date>=CURDATE()", (data["event_id"],))
    if not cur.fetchone():
        cur.close(); db.close(); return err("Event not available for booking")

    # Lock seat
    cur.execute("SELECT * FROM seat WHERE seat_id=%s AND status='available'", (data["seat_id"],))
    seat = cur.fetchone()
    if not seat:
        cur.close(); db.close(); return err("Seat is not available", 409)

    try:
        cur2 = db.cursor()
        cur2.execute("UPDATE seat SET status='reserved' WHERE seat_id=%s", (data["seat_id"],))
        ref = generate_booking_ref()
        cur2.execute("""INSERT INTO booking (customer_id,event_id,seat_id,booking_ref,status)
                        VALUES (%s,%s,%s,%s,'pending')""",
                     (data["customer_id"], data["event_id"], data["seat_id"], ref))
        bid = cur2.lastrowid
        cur2.execute("INSERT INTO payment (booking_id,amount,payment_method,status) VALUES (%s,%s,%s,'pending')",
                     (bid, seat["price"], data["payment_method"]))
        db.commit(); cur.close(); cur2.close(); db.close()
        return ok({"booking_id": bid, "booking_ref": ref,
                   "amount": float(seat["price"]), "category": seat["category"]},
                  "Booking created — complete payment to confirm", 201)
    except Exception as e:
        db.rollback(); cur.close(); db.close()
        return err(str(e))

@app.route("/bookings/<int:bid>/confirm", methods=["POST"])
def confirm_booking(bid):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""SELECT b.seat_id, p.payment_id
                   FROM booking b JOIN payment p ON p.booking_id=b.booking_id
                   WHERE b.booking_id=%s AND b.status='pending'""", (bid,))
    row = cur.fetchone()
    if not row:
        cur.close(); db.close(); return err("Booking not found or already processed", 404)
    cur2 = db.cursor()
    cur2.execute("UPDATE booking SET status='confirmed' WHERE booking_id=%s", (bid,))
    cur2.execute("UPDATE seat SET status='booked' WHERE seat_id=%s", (row["seat_id"],))
    cur2.execute("UPDATE payment SET status='paid', paid_at=NOW() WHERE payment_id=%s", (row["payment_id"],))
    db.commit(); cur.close(); cur2.close(); db.close()
    return ok(message="Booking confirmed and payment recorded")

@app.route("/bookings/<int:bid>/cancel", methods=["POST"])
def cancel_booking(bid):
    data = request.get_json() or {}
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""SELECT b.seat_id, p.payment_id, p.status AS pay_status
                   FROM booking b JOIN payment p ON p.booking_id=b.booking_id
                   WHERE b.booking_id=%s AND b.status IN ('pending','confirmed')""", (bid,))
    row = cur.fetchone()
    if not row:
        cur.close(); db.close(); return err("Booking not found or already cancelled", 404)
    try:
        cur2 = db.cursor()
        cur2.execute("UPDATE booking SET status='cancelled',cancelled_at=NOW(),cancel_reason=%s WHERE booking_id=%s",
                     (data.get("reason"), bid))
        cur2.execute("UPDATE seat SET status='available' WHERE seat_id=%s", (row["seat_id"],))
        if row["pay_status"] == "paid":
            cur2.execute("UPDATE payment SET status='refunded',refunded_at=NOW() WHERE payment_id=%s", (row["payment_id"],))
        db.commit(); cur.close(); cur2.close(); db.close()
        return ok(message="Booking cancelled. Seat released." +
                  (" Refund initiated." if row["pay_status"]=="paid" else ""))
    except Exception as e:
        db.rollback(); cur.close(); db.close(); return err(str(e))

@app.route("/bookings/<string:ref>", methods=["GET"])
def get_booking(ref):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT b.*, c.full_name, c.email,
               e.event_name, e.event_date, e.event_time,
               v.name AS venue_name,
               s.row_label, s.seat_number, s.category, s.price,
               p.status AS payment_status, p.payment_method, p.paid_at
        FROM booking b
        JOIN customer c ON b.customer_id=c.customer_id
        JOIN event e    ON b.event_id=e.event_id
        JOIN venue v    ON e.venue_id=v.venue_id
        JOIN seat s     ON b.seat_id=s.seat_id
        LEFT JOIN payment p ON p.booking_id=b.booking_id
        WHERE b.booking_ref=%s
    """, (ref,))
    row = cur.fetchone(); cur.close(); db.close()
    return ok(row) if row else err("Booking not found", 404)


# ════════════════════════════════════════════
#  PAYMENTS
# ════════════════════════════════════════════
@app.route("/payments/<int:bid>", methods=["GET"])
def get_payment(bid):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM payment WHERE booking_id=%s", (bid,))
    row = cur.fetchone(); cur.close(); db.close()
    return ok(row) if row else err("Payment not found", 404)


# ════════════════════════════════════════════
#  STATS
# ════════════════════════════════════════════
@app.route("/stats", methods=["GET"])
def get_stats():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS n FROM customer");          customers = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM event WHERE status='upcoming'"); upcoming = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM booking WHERE status='confirmed'"); confirmed = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM booking WHERE status='cancelled'"); cancelled = cur.fetchone()["n"]
    cur.execute("SELECT SUM(amount) AS t FROM payment WHERE status='paid'"); rev = cur.fetchone()["t"] or 0
    cur.execute("""SELECT category,
                          COUNT(*) AS total,
                          SUM(status='booked') AS booked,
                          SUM(status='available') AS available
                   FROM seat GROUP BY category""")
    capacity = cur.fetchall(); cur.close(); db.close()
    return ok({
        "total_customers": customers,
        "upcoming_events": upcoming,
        "confirmed_bookings": confirmed,
        "cancelled_bookings": cancelled,
        "total_revenue": float(rev),
        "capacity_by_category": capacity
    })


# ════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🎟  Ticket API running → http://localhost:{port}")
    app.run(host="0.0.0.0", port=port)
