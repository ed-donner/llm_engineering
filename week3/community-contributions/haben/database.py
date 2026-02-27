"""
Database Models and Connection Utilities

SQLAlchemy models and database connection for meeting_transcripts table.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, TIMESTAMP, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from dotenv import load_dotenv
import uuid

# Load .env from project root (4 levels up: haben -> community-contributions -> week3 -> llm_engineering)
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    # Fallback to local .env if global doesn't exist
    load_dotenv(override=True)

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'andela_ai_engineering_bootcamp')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

# Create database URL
# Handle password encoding for special characters
from urllib.parse import quote_plus

if DB_PASSWORD:
    password_encoded = quote_plus(str(DB_PASSWORD))
    DATABASE_URL = f"postgresql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    # No password (local development) - use peer authentication
    DATABASE_URL = f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class MeetingTranscript(Base):
    """SQLAlchemy model for meeting_transcripts table."""
    
    __tablename__ = 'meeting_transcripts'
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    original_text = Column(Text, nullable=True)
    cleaned_text = Column(Text, nullable=True)
    speaker = Column(String(100), nullable=True, index=True)
    chunk_index = Column(Integer, nullable=True)
    start_time = Column(TIMESTAMP, nullable=True)
    end_time = Column(TIMESTAMP, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    transcribed_at = Column(TIMESTAMP, default=datetime.now, nullable=True)
    llm_summary = Column(JSON, nullable=True)
    is_final = Column(Boolean, default=False, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.now, nullable=True)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now, nullable=True)
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'call_id': str(self.call_id),
            'title': self.title,
            'original_text': self.original_text,
            'cleaned_text': self.cleaned_text,
            'speaker': self.speaker,
            'chunk_index': self.chunk_index,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration_seconds,
            'transcribed_at': self.transcribed_at.isoformat() if self.transcribed_at else None,
            'llm_summary': self.llm_summary,
            'is_final': self.is_final,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_transcript_chunk(
    call_id: str,
    original_text: str,
    speaker: str = None,
    chunk_index: int = None,
    start_time: datetime = None,
    end_time: datetime = None,
    cleaned_text: str = None,
    llm_summary: dict = None
) -> bool:
    """
    Save a transcript chunk to the database.
    
    Args:
        call_id: UUID string of the call
        original_text: Raw transcription text
        speaker: Speaker label
        chunk_index: Sequential chunk number
        start_time: Start timestamp
        end_time: End timestamp
        cleaned_text: Post-processed text
        llm_summary: LLM-generated summary/analysis
        
    Returns:
        True if successful, False otherwise
    """
    db = SessionLocal()
    try:
        transcript = MeetingTranscript(
            call_id=uuid.UUID(call_id),
            original_text=original_text,
            cleaned_text=cleaned_text,
            speaker=speaker,
            chunk_index=chunk_index,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=(end_time - start_time).total_seconds() if start_time and end_time else None,
            llm_summary=llm_summary
        )
        db.add(transcript)
        db.commit()
        return True
    except Exception as e:
        print(f"Error saving transcript chunk: {e}")
        db.rollback()
        return False
    finally:
        db.close()
