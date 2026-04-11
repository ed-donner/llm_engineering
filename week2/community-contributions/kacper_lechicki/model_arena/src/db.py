"""
SQLite persistence for arena sessions (prompts, responses, judge evaluation).
"""

import json
import sqlite3

from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("data") / "arena.db"


def init_db() -> None:
    """Ensure the DB file exists and create the sessions table if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                prompt TEXT NOT NULL,
                system_prompt TEXT,
                models TEXT NOT NULL,
                responses TEXT NOT NULL,
                evaluation TEXT,
                winner TEXT
            )
        """)


def save_session(
    prompt: str,
    system_prompt: str,
    responses: list[dict],
    evaluation: dict,
) -> int:
    """Insert one session row; return its id."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO sessions
                (created_at, prompt, system_prompt, models,
                 responses, evaluation, winner)
            VALUES
                (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                prompt,
                system_prompt or "",
                json.dumps([r["model"] for r in responses]),
                json.dumps(responses),
                json.dumps(evaluation),
                evaluation.get("winner"),
            ),
        )

        session_id = cursor.lastrowid

    if session_id is None:
        raise RuntimeError("SQLite INSERT did not return a row id")

    return session_id


def clear_history() -> None:
    """Delete all sessions from the database."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM sessions")


def get_history(limit: int = 50) -> list[dict]:
    """Return recent sessions, newest first, with JSON columns parsed."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

    result = []

    for row in rows:
        d = dict(row)
        d["models"] = json.loads(d["models"])
        d["responses"] = json.loads(d["responses"])

        d["evaluation"] = (
            json.loads(d["evaluation"]) if d["evaluation"] else None
        )

        result.append(d)

    return result
