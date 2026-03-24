import sqlite3
from datetime import datetime, timedelta

DB = "clinic.db"

def init_db():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # --- Create schema ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialty TEXT NOT NULL,
        email TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctor_availability (
        availability_id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER NOT NULL,
        day_of_week TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        clinic_location TEXT,
        FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS availability_slots (
        slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
        availability_id INTEGER NOT NULL,
        day_of_week TEXT NOT NULL,
        start_time TEXT NOT NULL,
        is_booked INTEGER DEFAULT 0,
        FOREIGN KEY (availability_id) REFERENCES doctor_availability(availability_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        slot_id INTEGER NOT NULL,
        reason TEXT,
        status TEXT DEFAULT 'confirmed',
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
        FOREIGN KEY (slot_id) REFERENCES availability_slots(slot_id)
    )
    """)

    # --- Seed doctors ---
    cursor.executemany("""
    INSERT INTO doctors (name, specialty, email)
    VALUES (?, ?, ?)
    """, [
        ("Dr. Lim Wei", "Dermatology", "lim.wei@clinic.com"),
        ("Dr. Aisha Rahman", "Cardiology", "aisha.rahman@clinic.com"),
        ("Dr. Chen Yong", "Pediatrics", "chen.yong@clinic.com"),
        ("Dr. Kavitha Menon", "Orthopedics", "kavitha.menon@clinic.com")
    ])

    # --- Seed patients ---
    cursor.executemany("""
    INSERT INTO patients (name, email, phone)
    VALUES (?, ?, ?)
    """, [
        ("Nora Tan", "nora.tan@example.com", "012-3456789"),
        ("Ahmad Zulkifli", "ahmad.zulkifli@example.com", "013-9876543"),
        ("Mei Ling", "mei.ling@example.com", "014-2233445"),
        ("Raj Kumar", "raj.kumar@example.com", "015-5566778")
    ])

    # --- Seed doctor availability ---
    cursor.executemany("""
    INSERT INTO doctor_availability (doctor_id, day_of_week, start_time, end_time, clinic_location)
    VALUES (?, ?, ?, ?, ?)
    """, [
        (1, "Monday", "09:00", "17:00", "Main Clinic"),
        (1, "Wednesday", "09:00", "13:00", "Main Clinic"),
        (2, "Tuesday", "10:00", "16:00", "Main Clinic"),
        (3, "Friday", "09:00", "15:00", "Children’s Wing"),
        (4, "Thursday", "11:00", "18:00", "Main Clinic")
    ])

    # --- Generate slots automatically ---
    cursor.execute("SELECT availability_id, day_of_week, start_time, end_time FROM doctor_availability")
    availabilities = cursor.fetchall()

    for availability_id, day, start, end in availabilities:
        start_dt = datetime.strptime(start, "%H:%M")
        end_dt = datetime.strptime(end, "%H:%M")

        current = start_dt
        while current < end_dt:
            slot_time = current.strftime("%H:%M")
            cursor.execute("""
            INSERT INTO availability_slots (availability_id, day_of_week, start_time, is_booked)
            VALUES (?, ?, ?, 0)
            """, (availability_id, day, slot_time))
            current += timedelta(minutes=30)  # 30-min slots

    conn.commit()
    conn.close()
    print("Schema created, seed data inserted, and slots generated!")

if __name__ == "__main__":
    init_db()