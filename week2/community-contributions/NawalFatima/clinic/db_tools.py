import sqlite3

DB = "clinic.db"

def get_specialist_info(specialty: str):
    
    print(f"DATABASE TOOL CALLED: Getting specialist info for {specialty}", flush=True)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        # Normalize by comparing lowercase
        cursor.execute('SELECT name FROM doctors WHERE LOWER(specialty) = LOWER(?)', (specialty,))
        results = cursor.fetchall()

        if results:
            doctors = [row[0] for row in results]
            return f"Available {specialty} specialists: {', '.join(doctors)}"
        else:
            return f"No {specialty} specialist available at the moment"

def get_all_specialties():

    print(f"DATABASE TOOL CALLED: Getting all specialties info", flush=True)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT specialty FROM doctors;")
        specialties = [row[0] for row in cursor.fetchall()]

        return f"Available specialties: {', '.join(specialties)}"


def get_availability_slots(doctor_name):

    print(f"DATABASE TOOL CALLED: Getting availability slots for {doctor_name}", flush=True)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT doctor_id FROM doctors WHERE name = ?", (doctor_name,))
        result = cursor.fetchone()

        if result:
            doctor_id = result[0]
            cursor.execute("""
                SELECT s.slot_id, s.day_of_week, s.start_time, s.is_booked
                FROM availability_slots s
                JOIN doctor_availability d ON s.availability_id = d.availability_id
                WHERE d.doctor_id = ?
            """, (doctor_id,))
            slots = cursor.fetchall()

            if not slots:
                return f"No slots found for {doctor_name}"

            slot_lines = []
            for slot in slots:
                slot_id, day, start, is_booked = slot
                status = "Available" if is_booked == 0 else "Booked"
                slot_lines.append(f"{day} at {start} ({status})")
            print(f"SLOTS RETURNING: {slot_lines}", flush=True)  # was `result`, should be `slot_lines`
            return "\n".join(slot_lines)
        else:
            return "Doctor not found"




def book_appointment(patient_name, patient_email, patient_phone,
                     doctor_name, day_of_week, time, reason):
    conn = sqlite3.connect("clinic.db")
    cursor = conn.cursor()

    try:
    
        conn.execute("BEGIN")

     
        cursor.execute("SELECT patient_id FROM patients WHERE name = ?", (patient_name,))
        row = cursor.fetchone()
        if row:
            patient_id = row[0]
        else:
            cursor.execute("""
                INSERT INTO patients (name, email, phone)
                VALUES (?, ?, ?)
            """, (patient_name, patient_email, patient_phone))
            patient_id = cursor.lastrowid

  
        cursor.execute("""
            SELECT s.slot_id, s.is_booked, d.doctor_id
            FROM availability_slots s
            JOIN doctor_availability d ON s.availability_id = d.availability_id
            JOIN doctors doc ON d.doctor_id = doc.doctor_id
            WHERE doc.name = ? AND s.day_of_week = ? AND s.start_time = ?
        """, (doctor_name, day_of_week, time))
        slot = cursor.fetchone()
        if not slot:
            conn.rollback()
            return f"No slot found for {doctor_name} on {day_of_week} at {time}."

        slot_id, is_booked, doctor_id = slot
        if is_booked:
            conn.rollback()
            return f"Slot already booked for {doctor_name} on {day_of_week} at {time}."

      
        cursor.execute("""
            INSERT INTO appointments (patient_id, doctor_id, slot_id, reason, status)
            VALUES (?, ?, ?, ?, ?)
        """, (patient_id, doctor_id, slot_id, reason, "confirmed"))

        cursor.execute("UPDATE availability_slots SET is_booked = 1 WHERE slot_id = ?", (slot_id,))

        conn.commit()
        return f"Appointment booked: {patient_name} with {doctor_name} on {day_of_week} at {time} for {reason}."

    except Exception as e:
        conn.rollback()
        return f"Error booking appointment: {e}"
    finally:
        conn.close()


        
