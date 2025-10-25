"""
Persistent storage for conversation history using SQLite.
Stores all conversations with full turn history, metadata, and retrieval sources.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from contextlib import contextmanager

from app.diagnostics import get_logger

logger = get_logger(__name__)


class ConversationStorage:
    """Handles persistent storage of conversation history"""
    
    def __init__(self, db_path: str = "./data/conversations.db"):
        """
        Initialize conversation storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info(f"ConversationStorage initialized at {db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Create database schema if it doesn't exist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    last_active TEXT NOT NULL,
                    turn_count INTEGER DEFAULT 0,
                    title TEXT,
                    metadata TEXT
                )
            """)
            
            # Conversation turns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    sources TEXT,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id),
                    UNIQUE(session_id, turn_id)
                )
            """)
            
            # Create indices for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_last_active 
                ON sessions(last_active)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_turns_session_timestamp 
                ON turns(session_id, timestamp)
            """)
            
            # Migration: Add title column if it doesn't exist
            cursor.execute("PRAGMA table_info(sessions)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'title' not in columns:
                cursor.execute("ALTER TABLE sessions ADD COLUMN title TEXT")
                logger.info("Added title column to sessions table")
            
            logger.info("Database schema initialized successfully")
    
    def save_session(self, session_id: str, created_at: datetime, 
                     last_active: datetime, title: Optional[str] = None,
                     metadata: Optional[Dict] = None):
        """
        Save or update a conversation session.
        
        Args:
            session_id: Unique session identifier
            created_at: Session creation timestamp
            last_active: Last activity timestamp
            title: Optional conversation title
            metadata: Optional metadata dict
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (session_id, created_at, last_active, title, metadata)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    last_active = excluded.last_active,
                    title = COALESCE(excluded.title, sessions.title),
                    metadata = excluded.metadata
            """, (
                session_id,
                created_at.isoformat(),
                last_active.isoformat(),
                title,
                json.dumps(metadata) if metadata else None
            ))
            logger.debug(f"Saved session: {session_id}")
    
    def save_turn(self, session_id: str, turn_id: str, query: str, 
                  response: str, timestamp: datetime, 
                  sources: Optional[List[Dict]] = None,
                  metadata: Optional[Dict] = None):
        """
        Save a conversation turn.
        
        Args:
            session_id: Session this turn belongs to
            turn_id: Unique turn identifier
            query: User's query
            response: Assistant's response
            timestamp: Turn timestamp
            sources: Retrieved sources used for response
            metadata: Optional metadata dict
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Save the turn
            cursor.execute("""
                INSERT INTO turns (session_id, turn_id, query, response, timestamp, sources, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id, turn_id) DO UPDATE SET
                    query = excluded.query,
                    response = excluded.response,
                    timestamp = excluded.timestamp,
                    sources = excluded.sources,
                    metadata = excluded.metadata
            """, (
                session_id,
                turn_id,
                query,
                response,
                timestamp.isoformat(),
                json.dumps(sources) if sources else None,
                json.dumps(metadata) if metadata else None
            ))
            
            # Update session turn count and last_active
            cursor.execute("""
                UPDATE sessions 
                SET turn_count = (
                    SELECT COUNT(*) FROM turns WHERE session_id = ?
                ),
                last_active = ?
                WHERE session_id = ?
            """, (session_id, timestamp.isoformat(), session_id))
            
            logger.debug(f"Saved turn {turn_id} for session {session_id}")
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session information.
        
        Args:
            session_id: Session to retrieve
            
        Returns:
            Session dict or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, created_at, last_active, turn_count, title, metadata
                FROM sessions
                WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "session_id": row["session_id"],
                "created_at": row["created_at"],
                "last_active": row["last_active"],
                "turn_count": row["turn_count"],
                "title": row["title"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None
            }
    
    def get_session_turns(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Get all turns for a session.
        
        Args:
            session_id: Session to retrieve turns for
            limit: Optional limit on number of recent turns to return
            
        Returns:
            List of turn dicts ordered by timestamp
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if limit:
                query = """
                    SELECT turn_id, query, response, timestamp, sources, metadata
                    FROM turns
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                cursor.execute(query, (session_id, limit))
            else:
                query = """
                    SELECT turn_id, query, response, timestamp, sources, metadata
                    FROM turns
                    WHERE session_id = ?
                    ORDER BY timestamp ASC
                """
                cursor.execute(query, (session_id,))
            
            turns = []
            for row in cursor.fetchall():
                turns.append({
                    "turn_id": row["turn_id"],
                    "query": row["query"],
                    "response": row["response"],
                    "timestamp": row["timestamp"],
                    "sources": json.loads(row["sources"]) if row["sources"] else [],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None
                })
            
            # If we used DESC order for limit, reverse to get chronological order
            if limit:
                turns.reverse()
            
            return turns
    
    def get_all_sessions(self, limit: Optional[int] = None, 
                        order_by: str = "last_active DESC") -> List[Dict]:
        """
        Get all conversation sessions.
        
        Args:
            limit: Optional limit on number of sessions to return
            order_by: SQL ORDER BY clause (default: most recent first)
            
        Returns:
            List of session dicts
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = f"""
                SELECT session_id, created_at, last_active, turn_count, title, metadata
                FROM sessions
                ORDER BY {order_by}
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "session_id": row["session_id"],
                    "created_at": row["created_at"],
                    "last_active": row["last_active"],
                    "turn_count": row["turn_count"],
                    "title": row["title"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None
                })
            
            return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its turns.
        
        Args:
            session_id: Session to delete
            
        Returns:
            True if session was deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete turns first (foreign key constraint)
            cursor.execute("DELETE FROM turns WHERE session_id = ?", (session_id,))
            turns_deleted = cursor.rowcount
            
            # Delete session
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            session_deleted = cursor.rowcount > 0
            
            if session_deleted:
                logger.info(f"Deleted session {session_id} with {turns_deleted} turns")
            
            return session_deleted
    
    def delete_old_sessions(self, days: int = 30) -> int:
        """
        Delete sessions older than specified days.
        
        Args:
            days: Delete sessions inactive for this many days
            
        Returns:
            Number of sessions deleted
        """
        cutoff = datetime.now()
        from datetime import timedelta
        cutoff -= timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get sessions to delete
            cursor.execute("""
                SELECT session_id FROM sessions 
                WHERE last_active < ?
            """, (cutoff_str,))
            
            session_ids = [row["session_id"] for row in cursor.fetchall()]
            
            if session_ids:
                # Delete turns
                placeholders = ','.join('?' * len(session_ids))
                cursor.execute(f"""
                    DELETE FROM turns 
                    WHERE session_id IN ({placeholders})
                """, session_ids)
                
                # Delete sessions
                cursor.execute(f"""
                    DELETE FROM sessions 
                    WHERE session_id IN ({placeholders})
                """, session_ids)
                
                logger.info(f"Deleted {len(session_ids)} old sessions (inactive > {days} days)")
            
            return len(session_ids)
    
    def search_conversations(self, search_query: str, limit: int = 50) -> List[Dict]:
        """
        Search across all conversations for matching text.
        
        Args:
            search_query: Text to search for in queries and responses
            limit: Maximum number of results to return
            
        Returns:
            List of matching turns with session info
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            search_pattern = f"%{search_query}%"
            cursor.execute("""
                SELECT 
                    t.session_id, t.turn_id, t.query, t.response, 
                    t.timestamp, t.sources,
                    s.created_at as session_created
                FROM turns t
                JOIN sessions s ON t.session_id = s.session_id
                WHERE t.query LIKE ? OR t.response LIKE ?
                ORDER BY t.timestamp DESC
                LIMIT ?
            """, (search_pattern, search_pattern, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "session_id": row["session_id"],
                    "turn_id": row["turn_id"],
                    "query": row["query"],
                    "response": row["response"],
                    "timestamp": row["timestamp"],
                    "sources": json.loads(row["sources"]) if row["sources"] else [],
                    "session_created": row["session_created"]
                })
            
            return results
    
    def update_session_title(self, session_id: str, title: str):
        """
        Update the title of a conversation session.
        
        Args:
            session_id: Session to update
            title: New title for the session
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions 
                SET title = ?
                WHERE session_id = ?
            """, (title, session_id))
            logger.debug(f"Updated title for session {session_id}: {title}")
    
    def get_stats(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dict with stats about sessions and turns
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total sessions
            cursor.execute("SELECT COUNT(*) as count FROM sessions")
            total_sessions = cursor.fetchone()["count"]
            
            # Total turns
            cursor.execute("SELECT COUNT(*) as count FROM turns")
            total_turns = cursor.fetchone()["count"]
            
            # Average turns per session
            cursor.execute("""
                SELECT AVG(turn_count) as avg_turns 
                FROM sessions
            """)
            avg_turns = cursor.fetchone()["avg_turns"] or 0
            
            # Most recent session
            cursor.execute("""
                SELECT last_active 
                FROM sessions 
                ORDER BY last_active DESC 
                LIMIT 1
            """)
            recent = cursor.fetchone()
            most_recent = recent["last_active"] if recent else None
            
            return {
                "total_sessions": total_sessions,
                "total_turns": total_turns,
                "average_turns_per_session": round(avg_turns, 2),
                "most_recent_activity": most_recent,
                "database_path": str(self.db_path)
            }


# Global storage instance
_conversation_storage = None


def get_conversation_storage() -> ConversationStorage:
    """Get the global conversation storage instance"""
    global _conversation_storage
    if _conversation_storage is None:
        _conversation_storage = ConversationStorage()
    return _conversation_storage
