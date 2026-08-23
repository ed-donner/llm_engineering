import sqlite3
from contextlib import contextmanager


class DB:
    """Database class for the bot."""
    def __init__(self, db_path: str = "ai-call-assistant.db"):
        self.db_path = db_path
    
    @contextmanager
    def get_db(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=True)  # Disable thread check if your SQLite is THREADSAFE=1
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON;')
        conn.execute('PRAGMA journal_mode=WAL;') # WAL for concurrency
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def setup(self) -> None:
        """Setup the database tables."""
        # Add table calls [name, id]
        with self.get_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL            )
            """)
            # Add table questions [call_id (foreign key), question, answered, username, id]
            conn.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    call_id INTEGER NOT NULL,
                    question TEXT NOT NULL,
                    answered BOOLEAN NOT NULL DEFAULT 0,
                    username TEXT,
                    FOREIGN KEY (call_id) REFERENCES calls(id)
                )
            """)


    def get_calls(self) -> list[dict]:
        """Return all calls as list of (id, name) tuples."""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM calls")
            data = [dict(row) for row in cursor.fetchall()]
        return data

    def get_call_id_by_name(self, name: str) -> str:
        """Get the id of a call by name."""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM calls WHERE name = ?", (name,))
            data = cursor.fetchone()
        return data['id'] if data else None

    def add_call(self, name: str) -> None:
        """Add a new call to the database."""
        with self.get_db() as conn:
            conn.execute("""
                INSERT INTO calls (name) VALUES (?)
            """, (name,))

    # Participant will be adding questions to call they a part of - need a transactional utility method
    def add_question(self, call_name: str, question: str, username: str) -> None:
        """Add a new question to the database."""
        
        with self.get_db() as conn:

            conn.execute("""
            INSERT INTO questions (call_id, question, username) VALUES (?, ?, ?)
        """, (self.get_call_id_by_name(call_name), question, username))

    # Participant will be marking questions as answered - need a transactional utility method
    def mark_question_answered(self, question_id: int) -> None:
        """Mark a question as answered."""
        with self.get_db() as conn:
            conn.execute("""
                UPDATE questions SET answered = 1 WHERE id = ?
            """, (question_id,))

    def get_questions_by_username(self, username: str) -> list[dict]:
        """Get all questions from a user."""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, question, answered, username FROM questions WHERE username = ?
        """, (username,))
            data = [dict(row) for row in cursor.fetchall()]
        return data

    # Bot will need to get all non-answered questions from a call - need a utility method
    def get_non_answered_questions(self, name: str) -> list[dict]:
        """Get all non-answered questions from a call."""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, question, username FROM questions WHERE call_id = (SELECT id FROM calls WHERE name = ?) AND answered = 0
        """, (name,))
            data = [dict(row) for row in cursor.fetchall()]
        return data
        
    # Bot will need to get a selection of questions based on the ids provided - need a utility method
    def get_questions_by_ids(self, question_ids: list[int]) -> list[dict]:
        """Get a selection of questions based on the ids provided."""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM questions WHERE id IN (?)
        """, (question_ids,))
            data = [dict(row) for row in cursor.fetchall()]
        return data