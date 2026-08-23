import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv(override=True)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'andela_ai_engineering_bootcamp')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD')

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cur = conn.cursor()

# Create tables
print("Creating tables...")

cur.execute("""
CREATE TABLE IF NOT EXISTS flights (
    flight_id SERIAL PRIMARY KEY,
    flight_number VARCHAR(10) NOT NULL UNIQUE,
    origin VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    departure_time TIMESTAMP NOT NULL,
    arrival_time TIMESTAMP NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    airline_name VARCHAR(100) DEFAULT 'FlightAI',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    booking_id SERIAL PRIMARY KEY,
    flight_id INT REFERENCES flights(flight_id) ON DELETE CASCADE,
    passenger_name VARCHAR(100) NOT NULL,
    passenger_email VARCHAR(150),
    booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'confirmed'
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS passengers (
    passenger_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    loyalty_points INT DEFAULT 0,
    preferences JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS airports (
    airport_code CHAR(3) PRIMARY KEY,
    airport_name VARCHAR(150),
    city VARCHAR(100),
    country VARCHAR(100),
    timezone VARCHAR(50)
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS contributions (
    contribution_id SERIAL PRIMARY KEY,
    contributor_name VARCHAR(100) NOT NULL,
    contribution_type VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active'
);
""")

conn.commit()
print("Tables created successfully!")

# Insert demo data
print("Inserting demo data...")

# Insert airports
airports_data = [
    ('LHR', 'Heathrow Airport', 'London', 'United Kingdom', 'Europe/London'),
    ('CDG', 'Charles de Gaulle Airport', 'Paris', 'France', 'Europe/Paris'),
    ('NRT', 'Narita International Airport', 'Tokyo', 'Japan', 'Asia/Tokyo'),
    ('BER', 'Berlin Brandenburg Airport', 'Berlin', 'Germany', 'Europe/Berlin'),
    ('JFK', 'John F. Kennedy International Airport', 'New York', 'United States', 'America/New_York'),
    ('DXB', 'Dubai International Airport', 'Dubai', 'United Arab Emirates', 'Asia/Dubai'),
    ('SYD', 'Sydney Kingsford Smith Airport', 'Sydney', 'Australia', 'Australia/Sydney'),
    ('BOM', 'Chhatrapati Shivaji Maharaj International Airport', 'Mumbai', 'India', 'Asia/Kolkata'),
]

cur.executemany("""
INSERT INTO airports (airport_code, airport_name, city, country, timezone)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (airport_code) DO NOTHING;
""", airports_data)

# Insert flights
now = datetime.now()
flights_data = [
    ('FA101', 'London', 'Paris', now + timedelta(days=1, hours=10), now + timedelta(days=1, hours=12), 799.00),
    ('FA102', 'Paris', 'Tokyo', now + timedelta(days=2, hours=14), now + timedelta(days=3, hours=8), 1400.00),
    ('FA103', 'Berlin', 'New York', now + timedelta(days=3, hours=9), now + timedelta(days=3, hours=15), 1200.00),
    ('FA104', 'Dubai', 'Sydney', now + timedelta(days=4, hours=22), now + timedelta(days=5, hours=14), 1500.00),
    ('FA105', 'Mumbai', 'London', now + timedelta(days=5, hours=2), now + timedelta(days=5, hours=8), 1000.00),
    ('FA106', 'New York', 'Berlin', now + timedelta(days=6, hours=18), now + timedelta(days=7, hours=6), 499.00),
    ('FA107', 'Tokyo', 'Dubai', now + timedelta(days=7, hours=11), now + timedelta(days=7, hours=18), 1100.00),
    ('FA108', 'Sydney', 'Mumbai', now + timedelta(days=8, hours=6), now + timedelta(days=8, hours=14), 1300.00),
]

cur.executemany("""
INSERT INTO flights (flight_number, origin, destination, departure_time, arrival_time, price)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (flight_number) DO NOTHING;
""", flights_data)

# Insert passengers
passengers_data = [
    ('John Doe', 'john.doe@email.com', 500, '{"preferred_seat": "window", "meal": "vegetarian"}'),
    ('Jane Smith', 'jane.smith@email.com', 1200, '{"preferred_seat": "aisle", "meal": "kosher"}'),
    ('Bob Johnson', 'bob.johnson@email.com', 300, '{"preferred_seat": "window", "meal": "standard"}'),
    ('Alice Williams', 'alice.williams@email.com', 800, '{"preferred_seat": "aisle", "meal": "vegan"}'),
]

cur.executemany("""
INSERT INTO passengers (full_name, email, loyalty_points, preferences)
VALUES (%s, %s, %s, %s::jsonb)
ON CONFLICT (email) DO NOTHING;
""", passengers_data)

# Insert bookings
cur.execute("SELECT flight_id, flight_number FROM flights LIMIT 4")
flight_ids = cur.fetchall()

bookings_data = [
    (flight_ids[0][0], 'John Doe', 'john.doe@email.com', 'confirmed'),
    (flight_ids[1][0], 'Jane Smith', 'jane.smith@email.com', 'confirmed'),
    (flight_ids[2][0], 'Bob Johnson', 'bob.johnson@email.com', 'pending'),
    (flight_ids[3][0], 'Alice Williams', 'alice.williams@email.com', 'confirmed'),
]

cur.executemany("""
INSERT INTO bookings (flight_id, passenger_name, passenger_email, status)
VALUES (%s, %s, %s, %s);
""", bookings_data)

# Insert contributions
contributions_data = [
    ('Haben Eyasu', 'notebook', 'Week 2 airline assistant with tool calling', 'active'),
    ('Haben Eyasu', 'documentation', 'README and setup scripts', 'active'),
    ('Haben Eyasu', 'database', 'PostgreSQL schema and demo data', 'active'),
]

cur.executemany("""
INSERT INTO contributions (contributor_name, contribution_type, description, status)
VALUES (%s, %s, %s, %s);
""", contributions_data)

conn.commit()
print("Demo data inserted successfully!")

# Display summary
cur.execute("SELECT COUNT(*) FROM flights")
print(f"\nFlights: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM bookings")
print(f"Bookings: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM passengers")
print(f"Passengers: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM airports")
print(f"Airports: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM contributions")
print(f"Contributions: {cur.fetchone()[0]}")

cur.close()
conn.close()
print("\nDatabase setup complete!")
