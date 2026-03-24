import os
import sqlite3
import glob
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

load_dotenv(override=True)

DB_PATH = str(Path(__file__).parent.parent / "knowledge.db")
KNOWLEDGE_BASE = str(Path(__file__).parent.parent / "knowledge-base")

CALL_TYPES = {
    '1': 'Incoming', '2': 'Outgoing', '3': 'Missed',
    '4': 'Voicemail', '5': 'Rejected', '6': 'Blocked'
}



def parse_date(date_ms: str, readable_date: str = "") -> tuple[str, int]:
    try:
        ms = int(date_ms)
        if readable_date:
            return readable_date, ms
        ts = ms / 1000
        return datetime.fromtimestamp(ts).strftime("%d %b %Y %I:%M %p"), ms
    except:
        return date_ms, 0



def create_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact TEXT,
            address TEXT,
            direction TEXT,
            body TEXT,
            date_str TEXT,
            date_ms INTEGER,
            year TEXT,
            year_month TEXT,
            doc_type TEXT,
            source TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact TEXT,
            number TEXT,
            call_type TEXT,
            duration_seconds INTEGER,
            duration_str TEXT,
            date_str TEXT,
            date_ms INTEGER,
            year TEXT,
            year_month TEXT,
            source TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sms_date_ms ON sms(date_ms)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sms_contact ON sms(contact)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_calls_date_ms ON calls(date_ms)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_calls_contact ON calls(contact)")
    conn.commit()



def ingest_sms_to_sql(conn):
    folder = str(Path(KNOWLEDGE_BASE) / "sms")
    xml_files = glob.glob(str(Path(folder) / "*.xml"))
    count = 0

    for xml_file in xml_files:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # SMS
        for sms in root.findall('sms'):
            body = sms.get('body', '')
            if not body or body == 'null':
                continue

            contact = sms.get('contact_name', '(Unknown)')
            address = sms.get('address', '')
            sms_type = sms.get('type', '1')
            date_str, date_ms_int = parse_date(sms.get('date', '0'), sms.get('readable_date', ''))
            direction = "Received" if sms_type == '1' else "Sent"

            try:
                dt = datetime.fromtimestamp(date_ms_int / 1000)
                year = str(dt.year)
                year_month = dt.strftime("%B %Y")
            except:
                year, year_month = "", ""

            conn.execute("""
                INSERT INTO sms (contact, address, direction, body, date_str, date_ms, year, year_month, doc_type, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (contact, address, direction, body, date_str, date_ms_int, year, year_month, "sms", xml_file))
            count += 1

        # MMS
        for mms in root.findall('mms'):
            contact = mms.get('contact_name', '(Unknown)')
            address = mms.get('address', '')
            msg_box = mms.get('msg_box', '1')
            date_str, date_ms_int = parse_date(mms.get('date', '0'), mms.get('readable_date', ''))
            direction = "Received" if msg_box == '1' else "Sent"

            try:
                dt = datetime.fromtimestamp(date_ms_int / 1000)
                year = str(dt.year)
                year_month = dt.strftime("%B %Y")
            except:
                year, year_month = "", ""

            parts_text = []
            for part in mms.findall('.//part'):
                ct = part.get('ct', '')
                text_content = part.get('text', '')
                if 'text/plain' in ct and text_content and text_content != 'null':
                    parts_text.append(text_content)

            if not parts_text:
                continue

            body = "\n".join(parts_text)
            conn.execute("""
                INSERT INTO sms (contact, address, direction, body, date_str, date_ms, year, year_month, doc_type, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (contact, address, direction, body, date_str, date_ms_int, year, year_month, "mms", xml_file))
            count += 1

    conn.commit()
    print(f"  SQL SMS/MMS: inserted {count} records")


def ingest_calls_to_sql(conn):
    folder = str(Path(KNOWLEDGE_BASE) / "call")
    xml_files = glob.glob(str(Path(folder) / "*.xml"))
    count = 0

    for xml_file in xml_files:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for call in root.findall('call'):
            contact = call.get('contact_name', '(Unknown)')
            number = call.get('number', '')
            duration_sec = int(call.get('duration', 0))
            call_type = call.get('type', '1')
            date_str, date_ms_int = parse_date(call.get('date', '0'), call.get('readable_date', ''))
            call_type_label = CALL_TYPES.get(call_type, f"Type {call_type}")

            try:
                dt = datetime.fromtimestamp(date_ms_int / 1000)
                year = str(dt.year)
                year_month = dt.strftime("%B %Y")
            except:
                year, year_month = "", ""

            minutes = duration_sec // 60
            seconds = duration_sec % 60
            if duration_sec == 0:
                duration_str = "0 seconds (missed/rejected)"
            elif minutes > 0:
                duration_str = f"{minutes} min {seconds} sec"
            else:
                duration_str = f"{seconds} sec"

            conn.execute("""
                INSERT INTO calls (contact, number, call_type, duration_seconds, duration_str, date_str, date_ms, year, year_month, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (contact, number, call_type_label, duration_sec, duration_str, date_str, date_ms_int, year, year_month, xml_file))
            count += 1

    conn.commit()
    print(f"  SQL Calls: inserted {count} records")


def build_sql_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    ingest_sms_to_sql(conn)
    ingest_calls_to_sql(conn)
    conn.close()
    print(f"\nSQL DB built at {DB_PATH}")


#query functions

def query_sql(
    start_ms: int = None,
    end_ms: int = None,
    contact: str = None,
    doc_types: list[str] = None,
    limit: int = 50
) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    results = []

    query_sms = doc_types is None or "sms" in doc_types
    query_calls = doc_types is None or "calls" in doc_types

    if query_sms:
        query = "SELECT *, 'sms_table' as _table FROM sms WHERE 1=1"
        params = []
        if start_ms is not None:
            query += " AND date_ms >= ?"
            params.append(start_ms)
        if end_ms is not None:
            query += " AND date_ms <= ?"
            params.append(end_ms)
        if contact:
            query += " AND contact LIKE ?"
            params.append(f"%{contact}%")
        query += f" ORDER BY date_ms ASC LIMIT {limit}"
        rows = conn.execute(query, params).fetchall()
        results.extend([dict(r) for r in rows])

    if query_calls:
        query = "SELECT *, 'calls_table' as _table FROM calls WHERE 1=1"
        params = []
        if start_ms is not None:
            query += " AND date_ms >= ?"
            params.append(start_ms)
        if end_ms is not None:
            query += " AND date_ms <= ?"
            params.append(end_ms)
        if contact:
            query += " AND contact LIKE ?"
            params.append(f"%{contact}%")
        query += f" ORDER BY date_ms ASC LIMIT {limit}"
        rows = conn.execute(query, params).fetchall()
        results.extend([dict(r) for r in rows])

    conn.close()
    return results


def format_sql_results(results: list[dict]) -> str:
    """Format SQL results as readable context string."""
    if not results:
        return "No records found for the specified criteria."

    lines = []
    for r in results:
        if 'body' in r:
            role = "Me" if r['direction'] == 'Sent' else r['contact']
            lines.append(
                f"{r['doc_type'].upper()} Record | Date: {r['date_str']} | "
                f"Contact: {r['contact']} | Direction: {r['direction']}\n"
                f"Message: {role}: {r['body']}"
            )
        else:
            lines.append(
                f"Call Record | Date: {r['date_str']} | Contact: {r['contact']} | "
                f"Number: {r['number']} | Type: {r['call_type']} | Duration: {r['duration_str']}"
            )
    return "\n\n".join(lines)
