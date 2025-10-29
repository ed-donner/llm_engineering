"""SQLite database schema for Tuxedo Link."""

import sqlite3
from typing import Optional


SCHEMA_VERSION = 2

# SQL statements for creating tables
CREATE_ALERTS_TABLE = """
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    profile_json TEXT NOT NULL,
    frequency TEXT NOT NULL CHECK(frequency IN ('immediately', 'daily', 'weekly')),
    last_sent TIMESTAMP,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_match_ids TEXT DEFAULT '[]'
);
"""

CREATE_CATS_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS cats_cache (
    id TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL,
    source TEXT NOT NULL,
    data_json TEXT NOT NULL,
    image_embedding BLOB,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_duplicate BOOLEAN DEFAULT 0,
    duplicate_of TEXT,
    FOREIGN KEY (duplicate_of) REFERENCES cats_cache(id) ON DELETE SET NULL
);
"""

CREATE_SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Index statements
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_fingerprint ON cats_cache(fingerprint);",
    "CREATE INDEX IF NOT EXISTS idx_source ON cats_cache(source);",
    "CREATE INDEX IF NOT EXISTS idx_fetched_at ON cats_cache(fetched_at);",
    "CREATE INDEX IF NOT EXISTS idx_is_duplicate ON cats_cache(is_duplicate);",
    "CREATE INDEX IF NOT EXISTS idx_alerts_email ON alerts(user_email);",
    "CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(active);",
]


def initialize_database(db_path: str) -> None:
    """
    Initialize the database with all tables and indexes.
    
    Args:
        db_path: Path to SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create tables
        cursor.execute(CREATE_ALERTS_TABLE)
        cursor.execute(CREATE_CATS_CACHE_TABLE)
        cursor.execute(CREATE_SCHEMA_VERSION_TABLE)
        
        # Create indexes
        for index_sql in CREATE_INDEXES:
            cursor.execute(index_sql)
        
        # Check and set schema version
        cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        result = cursor.fetchone()
        
        if result is None:
            cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
        elif result[0] < SCHEMA_VERSION:
            # Future: Add migration logic here
            cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
        
        conn.commit()
        print(f"Database initialized successfully at {db_path}")
        
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to initialize database: {e}")
    
    finally:
        conn.close()


def drop_all_tables(db_path: str) -> None:
    """
    Drop all tables (useful for testing).
    
    Args:
        db_path: Path to SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DROP TABLE IF EXISTS cats_cache")
        cursor.execute("DROP TABLE IF EXISTS alerts")
        cursor.execute("DROP TABLE IF EXISTS schema_version")
        conn.commit()
        print("All tables dropped successfully")
        
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to drop tables: {e}")
    
    finally:
        conn.close()


if __name__ == "__main__":
    # For testing
    import os
    test_db = "test_database.db"
    
    if os.path.exists(test_db):
        os.remove(test_db)
    
    initialize_database(test_db)
    print(f"Test database created at {test_db}")

