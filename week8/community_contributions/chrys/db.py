"""SQLite audit log for ARIA runs (90-day retention)."""
import os
import sqlite3
from datetime import datetime, timezone
from typing import List

from models import DecisionRecord

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "aria_audit.db")


def _init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS run_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_utc TEXT NOT NULL,
            asset TEXT NOT NULL,
            tech_score INTEGER,
            sentiment TEXT,
            final_score REAL,
            decision TEXT NOT NULL,
            skip_reason TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def log_decisions(records: List[DecisionRecord]) -> None:
    _init_db()
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB_PATH)
    for r in records:
        conn.execute(
            """INSERT INTO run_log (ts_utc, asset, tech_score, sentiment, final_score, decision, skip_reason, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (now, r.asset, r.tech_score, r.sentiment, r.final_score, r.decision, r.skip_reason or "", now),
        )
    conn.commit()
    conn.close()


def purge_older_than_days(days: int = 90) -> int:
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None).timestamp() - (days * 86400)
    cutoff_str = datetime.utcfromtimestamp(cutoff).isoformat() + "Z"
    cur = conn.execute("DELETE FROM run_log WHERE created_at < ?", (cutoff_str,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted
