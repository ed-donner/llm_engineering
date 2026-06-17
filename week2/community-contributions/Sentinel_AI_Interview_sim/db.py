"""
db.py — SQLite Persistence for Sentinel AI Interview Simulator

Handles all database operations: sessions, questions, and analytics.
Uses the same simple pattern as Day 4 reference notebook.
"""

import sqlite3
from datetime import datetime

DB = "interview.db"


def init_db():
    """Create tables if they don't exist."""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_name TEXT DEFAULT 'Anonymous',
                domain TEXT,
                provider TEXT,
                started_at TEXT,
                ended_at TEXT,
                total_score REAL DEFAULT 0,
                questions_answered INTEGER DEFAULT 0,
                status TEXT DEFAULT 'in_progress'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                question_text TEXT,
                answer_text TEXT,
                score REAL,
                feedback TEXT,
                question_number INTEGER,
                asked_at TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')

        conn.commit()
    print("Database initialized successfully.")


def save_session(domain, provider, candidate_name="Anonymous"):
    """Create a new interview session. Returns the session ID."""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO sessions (candidate_name, domain, provider, started_at) VALUES (?, ?, ?, ?)',
            (candidate_name, domain, provider, datetime.now().isoformat())
        )
        conn.commit()
        session_id = cursor.lastrowid
    print(f"Session {session_id} created for {candidate_name} — domain: {domain}, provider: {provider}")
    return session_id


def save_question(session_id, question_text, answer_text, score, feedback, question_number):
    """Save a question-answer pair with its score."""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO questions 
               (session_id, question_text, answer_text, score, feedback, question_number, asked_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (session_id, question_text, answer_text, score, feedback, question_number, datetime.now().isoformat())
        )
        # Update session totals
        cursor.execute(
            '''UPDATE sessions 
               SET total_score = total_score + ?, questions_answered = questions_answered + 1 
               WHERE id = ?''',
            (score, session_id)
        )
        conn.commit()
    print(f"Q{question_number} saved — score: {score}/10")


def end_session(session_id, status="completed"):
    """Mark a session as ended."""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE sessions SET ended_at = ?, status = ? WHERE id = ?',
            (datetime.now().isoformat(), status, session_id)
        )
        conn.commit()
    print(f"Session {session_id} ended — status: {status}")


def get_session_summary(session_id):
    """Get a summary of a session's performance."""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()

        # Session info
        cursor.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
        session = cursor.fetchone()
        if not session:
            return "No session found with that ID."

        # Questions
        cursor.execute(
            'SELECT question_number, score, feedback FROM questions WHERE session_id = ? ORDER BY question_number',
            (session_id,)
        )
        questions = cursor.fetchall()

        avg_score = session[6] / session[7] if session[7] > 0 else 0  # total_score / questions_answered

        summary = f"Session {session_id} — {session[1]} ({session[2]})\n"
        summary += f"Provider: {session[3]} | Status: {session[8]}\n"
        summary += f"Questions answered: {session[7]} | Avg score: {avg_score:.1f}/10\n"
        summary += "-" * 40 + "\n"

        for q in questions:
            summary += f"  Q{q[0]}: {q[1]}/10 — {q[2]}\n"

        return summary


def get_all_sessions():
    """Get a list of all sessions for display."""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, candidate_name, domain, provider, questions_answered, total_score, status FROM sessions ORDER BY id DESC'
        )
        sessions = cursor.fetchall()

    if not sessions:
        return "No sessions found."

    result = "Past Interview Sessions:\n" + "=" * 50 + "\n"
    for s in sessions:
        avg = s[5] / s[4] if s[4] > 0 else 0
        result += f"  #{s[0]} | {s[1]} | {s[2]} | {s[3]} | {s[4]} Qs | Avg: {avg:.1f}/10 | {s[6]}\n"

    return result
