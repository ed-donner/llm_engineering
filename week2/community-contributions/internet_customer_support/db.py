"""SQLite persistence for the ISP internet customer support demo."""

from __future__ import annotations

import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional

DB_FILENAME = "isp_support.db"


def db_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILENAME)


@contextmanager
def get_connection():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                account_id TEXT PRIMARY KEY,
                phone TEXT NOT NULL UNIQUE,
                customer_name TEXT,
                plan_name TEXT NOT NULL,
                data_remaining_gb REAL NOT NULL,
                data_cap_gb REAL NOT NULL,
                billing_cycle_end TEXT,
                line_status TEXT NOT NULL DEFAULT 'active',
                modem_last_seen TEXT,
                region TEXT
            );

            CREATE TABLE IF NOT EXISTS service_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT DEFAULT 'info',
                starts_at TEXT,
                ends_at TEXT
            );

            CREATE TABLE IF NOT EXISTS support_sessions (
                session_id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                summary TEXT,
                image_prompt TEXT
            );

            CREATE TABLE IF NOT EXISTS session_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES support_sessions(session_id)
            );

            CREATE INDEX IF NOT EXISTS idx_session_messages_session
            ON session_messages(session_id);

            CREATE TABLE IF NOT EXISTS support_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                note TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


def seed_demo_data() -> None:
    """Insert demo rows if tables are empty."""
    with get_connection() as conn:
        cur = conn.execute("SELECT COUNT(*) FROM accounts")
        if cur.fetchone()[0] > 0:
            return

        accounts = [
            (
                "NL-10042",
                "+15551234001",
                "Alex Rivera",
                "Fiber 500",
                120.5,
                500.0,
                "2026-04-28",
                "active",
                "2026-04-02T08:15:00",
                "West Coast",
            ),
            (
                "NL-10088",
                "+15559876543",
                "Jordan Kim",
                "Cable 200",
                3.2,
                200.0,
                "2026-04-15",
                "active",
                "2026-04-01T12:00:00",
                "Midwest",
            ),
            (
                "NL-10102",
                "+15550001122",
                "Sam Patel",
                "Fiber 1G",
                0.0,
                1024.0,
                "2026-04-20",
                "throttled",
                "2026-04-02T06:00:00",
                "Northeast",
            ),
        ]
        conn.executemany(
            """
            INSERT INTO accounts (
                account_id, phone, customer_name, plan_name,
                data_remaining_gb, data_cap_gb, billing_cycle_end,
                line_status, modem_last_seen, region
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            accounts,
        )

        events = [
            (
                "West Coast",
                "maintenance",
                "Planned fiber maintenance 2am–5am local; brief blips possible.",
                "info",
                "2026-04-03T02:00:00",
                "2026-04-03T05:00:00",
            ),
            (
                "Northeast",
                "outage",
                "Localized outage in sector NE-7; crews assigned.",
                "warning",
                "2026-04-02T10:00:00",
                None,
            ),
        ]
        conn.executemany(
            """
            INSERT INTO service_events (region, event_type, message, severity, starts_at, ends_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            events,
        )


def lookup_account(account_id: Optional[str], phone: Optional[str]) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        if account_id and account_id.strip():
            row = conn.execute(
                "SELECT * FROM accounts WHERE lower(trim(account_id)) = lower(trim(?))",
                (account_id.strip(),),
            ).fetchone()
            return dict(row) if row else None
        if phone and phone.strip():
            raw = phone.strip()
            digits = "".join(c for c in raw if c.isdigit())
            tail = digits[-10:] if len(digits) >= 10 else digits
            row = conn.execute(
                "SELECT * FROM accounts WHERE phone = ? OR phone LIKE ?",
                (raw, f"%{tail}"),
            ).fetchone()
            return dict(row) if row else None
        return None


def get_events_for_region(region: Optional[str]) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if region:
            rows = conn.execute(
                """
                SELECT * FROM service_events
                WHERE region IS NULL OR lower(region) = lower(?)
                ORDER BY id DESC LIMIT 10
                """,
                (region,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM service_events ORDER BY id DESC LIMIT 10"
            ).fetchall()
        return [dict(r) for r in rows]


def create_session() -> str:
    sid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO support_sessions (session_id, started_at) VALUES (?, ?)",
            (sid, now),
        )
    return sid


def append_message(session_id: str, role: str, content: str) -> None:
    now = datetime.utcnow().isoformat() + "Z"
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO session_messages (session_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, role, content, now),
        )


def insert_support_note(account_id: str, note: str) -> int:
    now = datetime.utcnow().isoformat() + "Z"
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO support_notes (account_id, note, created_at)
            VALUES (?, ?, ?)
            """,
            (account_id.strip(), note.strip(), now),
        )
        return int(cur.lastrowid)


def end_session_record(
    session_id: str, summary: str, image_prompt: str
) -> None:
    now = datetime.utcnow().isoformat() + "Z"
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE support_sessions
            SET ended_at = ?, summary = ?, image_prompt = ?
            WHERE session_id = ?
            """,
            (now, summary, image_prompt, session_id),
        )
