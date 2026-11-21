#sqlite 
import sqlite3
from pathlib import Path
from unittest import result 
#that db file that sits next to the script
DB = Path(__file__).parent / "bookings.db"
#--------------------------------------------------------------------------------
#create tables; if not exist makes re running safe
with sqlite3.connect(DB) as conn:
    conn.execute((
        "create table if not exists PRICES(CITY TEXT PRIMARY KEY,PRICE REAL)")  
    )
    conn.execute("CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY, name TEXT, city TEXT, price REAL, status TEXT, booked_at TEXT)")
    #Ed starting price
    SEED = {"new york": 100.0, "cairo": 120.0, "london": 90.0, "berlin": 80.0, "kuala lumpur": 70.0}
#insert or ignore add city only if its not there so re running does not duplicate or overwrite.
    with sqlite3.connect(DB) as conn:
        for city, price in SEED.items():
            conn.execute("INSERT OR IGNORE INTO PRICES (CITY, PRICE) VALUES (?, ?)", (city, price))

#--------------------------------------------------------------------------------
# a function to get the price of a ticket for a given city
def get_ticket_price(city):
    print(f"DATABASE TOOL CALLED: Getting price for {city}", flush=True)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT PRICE FROM PRICES WHERE CITY = ?', (city.lower(),))
        result = cursor.fetchone()
    return f"Ticket price for {city} is ${result[0]}" if result else f"No price found for {city}"
#--------------------------------------------------------------------------------

# spy line to test! print(get_ticket_price("Cairo"))

#--------------------------------------------------------------------------------
# a function to set the price of a ticket for a given city
def set_ticket_price(city, price):
    print(f"DATABASE TOOL CALLED: Setting price for {city} to {price}", flush=True)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO PRICES (CITY, PRICE) VALUES (?, ?) ON CONFLICT(CITY) DO UPDATE SET PRICE = ?', (city.lower(), price, price))
    return f"Price for {city} set to ${price}"
#--------------------------------------------------------------------------------
#test update price print(set_ticket_price("Paris", 170))
# test get price print(get_ticket_price("Paris"))
#--------------------------------------------------------------------------------
# a function to book a ticket for a given name and city
def book_ticket(name, city):
    print(f"DATABASE TOOL CALLED: Booking {city} for {name}", flush=True)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT PRICE FROM PRICES WHERE CITY = ?', (city.lower(),))
        result = cursor.fetchone() 
        if not result:
            return f"No price found for {city}. Cannot book ticket."
        price = result[0]
        cursor.execute("INSERT INTO bookings (name, city, price, status, booked_at) VALUES (?, ?, ?, 'CONFIRMED', datetime('now'))", (name, city.lower(), price))
        return f"Booked! Reference BK-{cursor.lastrowid}: {name} to {city} for ${price}"

#test. print(book_ticket("Mostafa", "London"))
#test. print(book_ticket("Mostafa", "Tokyo"))