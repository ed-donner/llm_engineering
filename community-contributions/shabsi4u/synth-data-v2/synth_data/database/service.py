"""
Database service for CRUD operations.

Implements the Repository Pattern to encapsulate all database access logic.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, UTC
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session

from .models import Base, Generation
from ..config import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Service for database operations on Generation records.

    Handles connection management, CRUD operations, and queries.
    Uses Repository Pattern to keep database logic isolated.
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        session: Optional[Session] = None
    ):
        """
        Initialize database service.

        Args:
            database_url: SQLAlchemy database URL (uses config default if None)
            session: Existing session for testing (creates new if None)
        """
        if session:
            # Use provided session (for testing with in-memory DB)
            self.session = session
            self._owns_session = False
            self.engine = None  # FIX: Always set engine attribute
            self.database_url = None
        else:
            # Create new engine and session
            self.database_url = database_url or settings.DATABASE_URL
            self.engine = create_engine(self.database_url)
            self._create_tables()
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            self._owns_session = True

        logger.info("DatabaseService initialized")

    def _create_tables(self) -> None:
        """Create all tables if they don't exist."""
        Base.metadata.create_all(self.engine)
        logger.debug("Database tables created/verified")

    def save_generation(
        self,
        schema: Dict[str, Any],
        model_backend: str,
        num_records: int,
        data: Optional[List[Dict[str, Any]]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> int:
        """
        Save a generation to the database.

        Args:
            schema: The schema definition used
            model_backend: Backend identifier (e.g., "huggingface")
            num_records: Number of records requested
            data: Generated data (None if failed)
            success: Whether generation succeeded
            error_message: Error details if failed

        Returns:
            ID of the saved generation

        Example:
            >>> service = DatabaseService()
            >>> gen_id = service.save_generation(
            ...     schema={"name": {"type": "string"}},
            ...     model_backend="huggingface",
            ...     num_records=10,
            ...     data=[{"name": "Alice"}, {"name": "Bob"}]
            ... )
        """
        generation = Generation(
            schema_json=schema,
            model_backend=model_backend,
            num_records=num_records,
            data_json=data,
            success=success,
            error_message=error_message,
            created_at=datetime.now(UTC)
        )

        self.session.add(generation)
        self.session.commit()
        self.session.refresh(generation)

        logger.info(f"Saved generation {generation.id} ({num_records} records)")
        return generation.id

    def get_generation(self, generation_id: int) -> Optional[Generation]:
        """
        Retrieve a generation by ID.

        Args:
            generation_id: ID of the generation

        Returns:
            Generation object or None if not found
        """
        generation = self.session.query(Generation).filter_by(
            id=generation_id
        ).first()

        if generation:
            logger.debug(f"Retrieved generation {generation_id}")
        else:
            logger.warning(f"Generation {generation_id} not found")

        return generation

    def get_recent_generations(
        self,
        limit: int = 10,
        backend: Optional[str] = None,
        success_only: bool = False
    ) -> List[Generation]:
        """
        Get recent generations, ordered by creation date (newest first).

        Args:
            limit: Maximum number of generations to return
            backend: Filter by backend (None = all backends)
            success_only: If True, only return successful generations

        Returns:
            List of Generation objects
        """
        query = self.session.query(Generation)

        # Apply filters
        if backend:
            query = query.filter_by(model_backend=backend)
        if success_only:
            query = query.filter_by(success=True)

        # Order and limit
        query = query.order_by(desc(Generation.created_at)).limit(limit)

        results = query.all()
        logger.debug(f"Retrieved {len(results)} recent generations")
        return results

    def get_all_generations(self) -> List[Generation]:
        """
        Get all generations (use with caution on large databases).

        Returns:
            List of all Generation objects
        """
        results = self.session.query(Generation).order_by(
            desc(Generation.created_at)
        ).all()
        logger.debug(f"Retrieved all {len(results)} generations")
        return results

    def delete_generation(self, generation_id: int) -> bool:
        """
        Delete a generation by ID.

        Args:
            generation_id: ID of the generation to delete

        Returns:
            True if deleted, False if not found
        """
        generation = self.get_generation(generation_id)

        if generation:
            self.session.delete(generation)
            self.session.commit()
            logger.info(f"Deleted generation {generation_id}")
            return True
        else:
            logger.warning(f"Cannot delete: generation {generation_id} not found")
            return False

    def count_generations(self, backend: Optional[str] = None) -> int:
        """
        Count total generations.

        Args:
            backend: Filter by backend (None = all backends)

        Returns:
            Count of generations
        """
        query = self.session.query(Generation)
        if backend:
            query = query.filter_by(model_backend=backend)

        count = query.count()
        logger.debug(f"Total generations: {count}")
        return count

    def close(self) -> None:
        """Close the database session."""
        if self._owns_session and self.session:
            self.session.close()
            logger.debug("Database session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
