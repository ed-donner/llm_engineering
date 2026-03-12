import sqlite3
import threading

DB = "progress.db"


class ProgressTracker:
    """
    Tracks user progress for levels, lessons, exercises.
    Stores data in SQLite.
    """

    def __init__(self):

        # allow multi-thread access (required for Gradio)
        self.conn = sqlite3.connect(DB, check_same_thread=False)

        # lock prevents concurrent write corruption
        self.lock = threading.Lock()

        self._create_tables()

    def _create_tables(self):

        with self.lock:
            c = self.conn.cursor()

            c.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                username TEXT,
                level TEXT,
                category TEXT,
                exercise TEXT,
                pronunciation_score REAL,
                accent_score REAL,
                PRIMARY KEY(username, level, category, exercise)
            )
            """)

            self.conn.commit()

    def update(self, username, level, category, exercise, pronunciation_score, accent_score):

        with self.lock:
            c = self.conn.cursor()

            c.execute("""
                INSERT OR REPLACE INTO progress
                (username, level, category, exercise, pronunciation_score, accent_score)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, level, category, exercise, pronunciation_score, accent_score))

            self.conn.commit()

    def get_level_progress(self, username, level):

        with self.lock:
            c = self.conn.cursor()

            c.execute("""
                SELECT AVG(pronunciation_score) FROM progress
                WHERE username=? AND level=?
            """, (username, level))

            result = c.fetchone()[0]

        return result or 0

    def get_overall_progress(self, username):

        with self.lock:
            c = self.conn.cursor()

            c.execute("""
                SELECT AVG(pronunciation_score) FROM progress
                WHERE username=?
            """, (username,))

            result = c.fetchone()[0]

        return result or 0