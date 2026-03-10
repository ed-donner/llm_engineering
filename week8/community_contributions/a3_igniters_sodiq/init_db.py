import sqlite3

conn = sqlite3.connect("support.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    email TEXT,
    plan TEXT,
    status TEXT,
    balance INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    user_email TEXT,
    amount INTEGER,
    status TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue TEXT,
    status TEXT
)
""")

# seed data
users_data = []
orders_data = []

for i in range(1, 21):
    email = f"user{i}@example.com"
    plan = "Premium" if i % 2 == 0 else "Basic"
    status = "active"
    balance = 100 * i
    users_data.append((i, email, plan, status, balance))
    
    order_id = f"ORD{1000+i}"
    amount = 50 * i
    order_status = "paid" if i % 5 != 0 else "refunded"
    orders_data.append((order_id, email, amount, order_status))

cursor.executemany("INSERT INTO users VALUES (?,?,?,?,?)", users_data)
cursor.executemany("INSERT INTO orders VALUES (?,?,?,?)", orders_data)

conn.commit()
conn.close()

print("Database initialized")