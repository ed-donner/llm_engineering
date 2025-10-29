"""Database manager for Tuxedo Link."""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Generator, Dict, Any
import numpy as np
from contextlib import contextmanager

from models.cats import Cat, AdoptionAlert, CatProfile
from .schema import initialize_database


class DatabaseManager:
    """Manages all database operations for Tuxedo Link."""
    
    def __init__(self, db_path: str):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Create database directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Initialize database if it doesn't exist
        if not os.path.exists(db_path):
            initialize_database(db_path)
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for database connections.
        
        Yields:
            SQLite database connection with row factory enabled
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # ===== ALERT OPERATIONS =====
    
    def create_alert(self, alert: AdoptionAlert) -> int:
        """
        Create a new adoption alert.
        
        Args:
            alert: AdoptionAlert object
            
        Returns:
            Alert ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO alerts 
                   (user_email, profile_json, frequency, last_sent, active, last_match_ids)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    alert.user_email,
                    alert.profile.model_dump_json(),
                    alert.frequency,
                    alert.last_sent.isoformat() if alert.last_sent else None,
                    alert.active,
                    json.dumps(alert.last_match_ids)
                )
            )
            return cursor.lastrowid
    
    def get_alert(self, alert_id: int) -> Optional[AdoptionAlert]:
        """Get alert by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, user_email, profile_json, frequency, 
                          last_sent, active, created_at, last_match_ids
                   FROM alerts WHERE id = ?""",
                (alert_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_alert(row)
            return None
    
    def get_alerts_by_email(self, email: str, active_only: bool = False) -> List[AdoptionAlert]:
        """
        Get all alerts for a specific email address.
        
        Args:
            email: User email address
            active_only: If True, only return active alerts
            
        Returns:
            List of AdoptionAlert objects
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute(
                    """SELECT id, user_email, profile_json, frequency, 
                              last_sent, active, created_at, last_match_ids
                       FROM alerts WHERE user_email = ? AND active = 1
                       ORDER BY created_at DESC""",
                    (email,)
                )
            else:
                cursor.execute(
                    """SELECT id, user_email, profile_json, frequency, 
                              last_sent, active, created_at, last_match_ids
                       FROM alerts WHERE user_email = ?
                       ORDER BY created_at DESC""",
                    (email,)
                )
            
            return [self._row_to_alert(row) for row in cursor.fetchall()]
    
    def get_all_alerts(self, active_only: bool = False) -> List[AdoptionAlert]:
        """
        Get all alerts in the database.
        
        Args:
            active_only: If True, only return active alerts
            
        Returns:
            List of AdoptionAlert objects
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                query = """SELECT id, user_email, profile_json, frequency, 
                                 last_sent, active, created_at, last_match_ids
                          FROM alerts WHERE active = 1
                          ORDER BY created_at DESC"""
            else:
                query = """SELECT id, user_email, profile_json, frequency, 
                                 last_sent, active, created_at, last_match_ids
                          FROM alerts
                          ORDER BY created_at DESC"""
            
            cursor.execute(query)
            return [self._row_to_alert(row) for row in cursor.fetchall()]
    
    def get_active_alerts(self) -> List[AdoptionAlert]:
        """Get all active alerts across all users."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, user_email, profile_json, frequency, 
                          last_sent, active, created_at, last_match_ids
                   FROM alerts WHERE active = 1"""
            )
            return [self._row_to_alert(row) for row in cursor.fetchall()]
    
    def get_alert_by_id(self, alert_id: int) -> Optional[AdoptionAlert]:
        """
        Get a specific alert by its ID.
        
        Args:
            alert_id: Alert ID to retrieve
            
        Returns:
            AdoptionAlert object or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, user_email, profile_json, frequency, 
                          last_sent, active, created_at, last_match_ids
                   FROM alerts WHERE id = ?""",
                (alert_id,)
            )
            row = cursor.fetchone()
            return self._row_to_alert(row) if row else None
    
    def update_alert(self, alert_id: int, **kwargs) -> None:
        """Update alert fields."""
        allowed_fields = ['profile_json', 'frequency', 'last_sent', 'active', 'last_match_ids']
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                if field == 'last_sent' and isinstance(value, datetime):
                    values.append(value.isoformat())
                elif field == 'last_match_ids':
                    values.append(json.dumps(value))
                else:
                    values.append(value)
        
        if updates:
            values.append(alert_id)
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE alerts SET {', '.join(updates)} WHERE id = ?",
                    values
                )
    
    def delete_alert(self, alert_id: int) -> None:
        """Delete an alert."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
    
    def _row_to_alert(self, row: sqlite3.Row) -> AdoptionAlert:
        """
        Convert database row to AdoptionAlert object.
        
        Args:
            row: SQLite row object from alerts table
            
        Returns:
            AdoptionAlert object with parsed JSON fields
        """
        return AdoptionAlert(
            id=row['id'],
            user_email=row['user_email'],
            profile=CatProfile.model_validate_json(row['profile_json']),
            frequency=row['frequency'],
            last_sent=datetime.fromisoformat(row['last_sent']) if row['last_sent'] else None,
            active=bool(row['active']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            last_match_ids=json.loads(row['last_match_ids']) if row['last_match_ids'] else []
        )
    
    # ===== CAT CACHE OPERATIONS =====
    
    def cache_cat(self, cat: Cat, image_embedding: Optional[np.ndarray] = None) -> None:
        """
        Cache a cat in the database.
        
        Args:
            cat: Cat object
            image_embedding: Optional numpy array of image embedding
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Serialize image embedding if provided
            embedding_bytes = None
            if image_embedding is not None:
                embedding_bytes = image_embedding.tobytes()
            
            cursor.execute(
                """INSERT OR REPLACE INTO cats_cache 
                   (id, fingerprint, source, data_json, image_embedding, fetched_at, is_duplicate, duplicate_of)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cat.id,
                    cat.fingerprint,
                    cat.source,
                    cat.model_dump_json(),
                    embedding_bytes,
                    cat.fetched_at.isoformat(),
                    False,
                    None
                )
            )
    
    def get_cached_cat(self, cat_id: str) -> Optional[Tuple[Cat, Optional[np.ndarray]]]:
        """Get a cat from cache by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT data_json, image_embedding FROM cats_cache 
                   WHERE id = ? AND is_duplicate = 0""",
                (cat_id,)
            )
            row = cursor.fetchone()
            if row:
                cat = Cat.model_validate_json(row['data_json'])
                embedding = None
                if row['image_embedding']:
                    embedding = np.frombuffer(row['image_embedding'], dtype=np.float32)
                return cat, embedding
            return None
    
    def get_cats_by_fingerprint(self, fingerprint: str) -> List[Tuple[Cat, Optional[np.ndarray]]]:
        """Get all cats with a specific fingerprint."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT data_json, image_embedding FROM cats_cache 
                   WHERE fingerprint = ? AND is_duplicate = 0
                   ORDER BY fetched_at ASC""",
                (fingerprint,)
            )
            results = []
            for row in cursor.fetchall():
                cat = Cat.model_validate_json(row['data_json'])
                embedding = None
                if row['image_embedding']:
                    embedding = np.frombuffer(row['image_embedding'], dtype=np.float32)
                results.append((cat, embedding))
            return results
    
    def mark_as_duplicate(self, duplicate_id: str, canonical_id: str) -> None:
        """Mark a cat as duplicate of another."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE cats_cache SET is_duplicate = 1, duplicate_of = ? WHERE id = ?",
                (canonical_id, duplicate_id)
            )
    
    def get_all_cached_cats(self, exclude_duplicates: bool = True) -> List[Cat]:
        """Get all cached cats."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if exclude_duplicates:
                cursor.execute(
                    "SELECT data_json FROM cats_cache WHERE is_duplicate = 0 ORDER BY fetched_at DESC"
                )
            else:
                cursor.execute(
                    "SELECT data_json FROM cats_cache ORDER BY fetched_at DESC"
                )
            return [Cat.model_validate_json(row['data_json']) for row in cursor.fetchall()]
    
    def cleanup_old_cats(self, days: int = 30) -> int:
        """
        Remove cats older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of cats removed
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM cats_cache WHERE fetched_at < ?",
                (cutoff_date,)
            )
            return cursor.rowcount
    
    def get_cache_stats(self) -> dict:
        """Get statistics about the cat cache."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM cats_cache WHERE is_duplicate = 0")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM cats_cache WHERE is_duplicate = 1")
            duplicates = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT source) FROM cats_cache WHERE is_duplicate = 0")
            sources = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT source, COUNT(*) as count 
                FROM cats_cache 
                WHERE is_duplicate = 0 
                GROUP BY source
            """)
            by_source = {row['source']: row['count'] for row in cursor.fetchall()}
            
            return {
                'total_unique': total,
                'total_duplicates': duplicates,
                'sources': sources,
                'by_source': by_source
            }

