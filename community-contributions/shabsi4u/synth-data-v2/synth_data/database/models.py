"""
SQLAlchemy database models.

Defines the database schema for generation history tracking.
"""

from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Generation(Base):
    """
    Stores metadata and results for each synthetic data generation.

    Attributes:
        id: Auto-increment primary key
        created_at: Timestamp when generation was created (UTC)
        schema_json: The schema definition used for generation
        model_backend: Backend used (e.g., "huggingface", "ollama")
        num_records: Number of records requested
        data_json: The generated data (stored inline for MVP)
        success: Whether generation completed successfully
        error_message: Error details if generation failed
    """

    __tablename__ = "generations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    schema_json = Column(JSON, nullable=False)
    model_backend = Column(String(50), nullable=False, default="huggingface")
    num_records = Column(Integer, nullable=False)
    data_json = Column(JSON, nullable=True)  # Null if generation failed
    success = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        """String representation for debugging."""
        status = "success" if self.success else "failed"
        return (
            f"<Generation(id={self.id}, "
            f"backend='{self.model_backend}', "
            f"records={self.num_records}, "
            f"status={status})>"
        )

    def to_dict(self) -> dict:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the generation
        """
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "schema": self.schema_json,
            "model_backend": self.model_backend,
            "num_records": self.num_records,
            "data": self.data_json,
            "success": self.success,
            "error_message": self.error_message,
        }
