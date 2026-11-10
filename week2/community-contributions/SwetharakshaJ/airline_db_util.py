"""
Shared SQLite-backed DB layer for the FlightAI airline exercises (week2).

Extracted from AirlineDbUtil.ipynb so it can be imported by multiple notebooks
(e.g. day4-AirlineChatbot.ipynb) instead of being copy-pasted into each one.

Usage:
    import sys
    sys.path.append(".")  # if importing from a notebook in the week2/ folder
    from airline_db_util import get_ticket_price, set_ticket_price, ...
"""

import sqlite3
import uuid

DB = "ticket-prices.db"

with sqlite3.connect(DB) as conn:
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS prices (city TEXT PRIMARY KEY, price REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS user (name TEXT PRIMARY KEY, payment_mode TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS booking (id TEXT PRIMARY KEY, user TEXT, destination TEXT, seat_count INTEGER, booking_value REAL)")
    conn.commit()


def get_ticket_price(city):
    print(f"DB TOOL CALLED: Getting price for {city}", flush=True)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT price FROM prices WHERE city = ?', (city.lower(),))
        result = cursor.fetchone()
        return f"Ticket price to {city} is ${result[0]}" if result else "No price data available for this city"


def set_ticket_price(city, price):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO prices (city, price) VALUES (?, ?) ON CONFLICT(city) DO UPDATE SET price = ?', (city.lower(), price, price))
        conn.commit()
        return f"Ticket price to {city} is updated in my databse to be ${price}"


def get_price_value(city):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT price FROM prices WHERE city = ?', (city.lower(),))
        result = cursor.fetchone()
        return result[0] if result else None


def set_user_details(name, paymentMode):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user (name, payment_mode) VALUES (?, ?) ON CONFLICT(name) DO UPDATE SET payment_mode = ?', (name, paymentMode, paymentMode))
        conn.commit()
        return f"Payment mode for user:  {name} is updated in my databse to be ${paymentMode}"


def set_booking_details(user, destination, seatCount):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()

        # calculate booking value
        price = get_price_value(destination)
        if price is None:
            return f"No price data available for {destination}; cannot create booking"
        booking_value = seatCount * price

        # generate ID
        booking_id = str(uuid.uuid4())

        cursor.execute('INSERT INTO booking (id, user, destination, seat_count, booking_value) VALUES (?, ?, ?, ?, ?)', (booking_id, user.lower(), destination.lower(), seatCount, booking_value))
        conn.commit()
        return f"Booking {booking_id} confirmed: {seatCount} seat(s) to {destination} for ${booking_value}"


def get_booking_details(user, destination=None):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        if destination is None:
            cursor.execute('SELECT * FROM booking WHERE user = ?', (user.lower(),))
            results = cursor.fetchall()
        else:
            cursor.execute('SELECT * FROM booking WHERE user = ? AND destination = ?', (user.lower(), destination.lower()))
            results = cursor.fetchall()

        if not results:
            return f"No booking found for {user}" + (f" to {destination}" if destination else "")

        lines = [
            f"Booking {b_id}: {b_user} has {seat_count} seat(s) to {b_dest} for a total of ${b_value}"
            for b_id, b_user, b_dest, seat_count, b_value in results
        ]
        return "\n".join(lines)



# Populate prices and users for a few demo entries. Runs on import (upserts are
# idempotent, so re-importing/re-running just resets these back to the demo values).
ticket_prices = {"london": 799, "paris": 899, "tokyo": 1420, "sydney": 2999}
for city, price in ticket_prices.items():
    set_ticket_price(city, price)

users = {"adam": "creditcard", "eva": "bank transfer", "marco": "creditcard", "zoya": "debitcard"}
for name, paymentMode in users.items():
    set_user_details(name, paymentMode)
