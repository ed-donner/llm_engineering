"""sqlite3 persistence for travel plans."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "travel_planner.db"


def init_db():
    """Create users_trips table if not exists."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users_trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            destination TEXT,
            days INTEGER,
            budget INTEGER,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_trip(user_id: str, destination: str, days: int, budget: int, response: str):
    """Store a trip request and its generated response."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO users_trips (user_id, destination, days, budget, response) VALUES (?, ?, ?, ?, ?)",
        (user_id, destination, days, budget, response),
    )
    conn.commit()
    conn.close()
