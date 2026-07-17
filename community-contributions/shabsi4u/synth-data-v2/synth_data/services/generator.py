"""Synthetic data generation orchestration service."""

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from ..backends.base import ModelBackend, GenerationParams, GenerationResult
from ..database.service import DatabaseService
from ..exceptions import SchemaValidationError, GenerationError

logger = logging.getLogger(__name__)


class GeneratorService:
    """Orchestrates synthetic data generation using backends and database."""

    def __init__(
        self,
        backend: ModelBackend,
        database: Optional[DatabaseService] = None,
        save_to_db: bool = True
    ):
        """Initialize with backend and optional database."""
        self.backend = backend
        self.save_to_db = save_to_db

        if save_to_db:
            if database:
                self.database = database
                self._owns_database = False
            else:
                self.database = DatabaseService()
                self._owns_database = True
        else:
            self.database = database
            self._owns_database = False

    def generate(
        self,
        schema: Dict[str, Any],
        num_records: int,
        params: Optional[GenerationParams] = None,
        on_progress: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """Generate synthetic data based on schema."""
        try:
            self._validate_schema(schema)
        except SchemaValidationError as e:
            logger.error(f"Schema validation failed: {e}")
            if self.save_to_db and self.database:
                self._save_failed_generation(
                    schema=schema,
                    num_records=num_records,
                    error_message=f"Schema validation failed: {str(e)}"
                )
            raise

        if num_records < 1:
            raise GenerationError(f"num_records must be >= 1, got {num_records}")

        if on_progress:
            try:
                on_progress(0, num_records)
            except Exception as e:
                logger.warning(f"Progress callback raised exception: {e}", exc_info=True)

        try:
            result: GenerationResult = self.backend.generate(
                schema=schema,
                num_records=num_records,
                params=params
            )

            # Step 4: Call progress callback (100% complete)
            # FIX: Protect against callback exceptions
            if on_progress:
                try:
                    on_progress(result.num_records, num_records)
                except Exception as e:
                    logger.warning(f"Progress callback raised exception: {e}", exc_info=True)

        except Exception as e:
            # Catch any backend errors and wrap them
            error_msg = f"Backend generation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Save failed attempt to database
            if self.save_to_db and self.database:
                gen_id = self._save_failed_generation(
                    schema=schema,
                    num_records=num_records,
                    error_message=error_msg
                )

                return {
                    "generation_id": gen_id,
                    "data": [],
                    "num_records": 0,
                    "success": False,
                    "error_message": error_msg,
                    "raw_response": "",
                    "backend": self.backend.__class__.__name__
                }
            else:
                # Re-raise if not saving to database
                raise GenerationError(error_msg) from e

        # Step 5: Save to database (if enabled)
        generation_id = None
        if self.save_to_db and self.database:
            try:
                generation_id = self._save_generation(
                    schema=schema,
                    num_records=num_records,
                    result=result
                )
                logger.info(f"Saved generation to database with ID: {generation_id}")
            except Exception as e:
                # Log database save errors but don't fail the generation
                # The user still gets their data even if DB save fails
                logger.error(f"Failed to save to database: {e}", exc_info=True)

        # Step 6: Return results
        return {
            "generation_id": generation_id,
            "data": result.data,
            "num_records": result.num_records,
            "success": result.success,
            "error_message": result.error_message,
            "raw_response": result.raw_response,
            "backend": self.backend.__class__.__name__
        }

    def _validate_schema(self, schema: Dict[str, Any]) -> None:
        """
        Validate schema structure before generation.

        This performs basic validation to catch common errors early.
        We don't need full JSON Schema validation for MVP - just enough
        to prevent obvious mistakes.

        Validation Rules:
        1. Schema must be a non-empty dictionary
        2. Each field must have a definition (dict or string)
        3. If field definition is a dict, it should have "type" key

        Args:
            schema: The schema to validate

        Raises:
            SchemaValidationError: If validation fails

        Examples:
            Valid schemas:
                {"name": {"type": "string"}}
                {"age": {"type": "integer", "minimum": 0}}
                {"status": "active"}  # Simple string allowed

            Invalid schemas:
                {}  # Empty
                {"name": None}  # None value
                {"name": {"no_type": "oops"}}  # Missing "type" key
        """
        # Rule 1: Schema must be a dict
        if not isinstance(schema, dict):
            raise SchemaValidationError(
                f"Schema must be a dictionary, got {type(schema).__name__}"
            )

        # Rule 2: Schema must not be empty
        if not schema:
            raise SchemaValidationError("Schema cannot be empty")

        # Rule 3: Validate each field
        for field_name, field_spec in schema.items():
            # Field name must be a string
            if not isinstance(field_name, str):
                raise SchemaValidationError(
                    f"Field names must be strings, got {type(field_name).__name__}"
                )

            # Field spec must be dict or string
            if field_spec is None:
                raise SchemaValidationError(
                    f"Field '{field_name}' has None value. "
                    f"Provide either a dict with 'type' or a string."
                )

            # If dict, should have "type" key (recommended but not required)
            if isinstance(field_spec, dict):
                if "type" not in field_spec:
                    logger.warning(
                        f"Field '{field_name}' missing 'type' key. "
                        f"LLM may not interpret it correctly."
                    )
            elif not isinstance(field_spec, str):
                logger.warning(
                    f"Field '{field_name}' has unusual type: "
                    f"{type(field_spec).__name__}. Expected dict or string."
                )

    def _save_generation(
        self,
        schema: Dict[str, Any],
        num_records: int,
        result: GenerationResult
    ) -> int:
        """
        Save successful generation to database.

        Args:
            schema: The schema used
            num_records: Number of records requested
            result: GenerationResult from backend

        Returns:
            Database ID of saved generation
        """
        # Save model info as "BackendName:model_id" for better tracking
        model_info = f"{self.backend.__class__.__name__}:{self.backend.model_id}"

        return self.database.save_generation(
            schema=schema,
            model_backend=model_info,
            num_records=num_records,
            data=result.data,
            success=result.success,
            error_message=result.error_message
        )

    def _save_failed_generation(
        self,
        schema: Dict[str, Any],
        num_records: int,
        error_message: str
    ) -> Optional[int]:
        """
        Save failed generation attempt to database.

        This is useful for:
        - Debugging: See what schemas/settings caused failures
        - Monitoring: Track success rate over time
        - User feedback: "Your last 3 attempts failed, here's why"

        Args:
            schema: The schema used
            num_records: Number of records requested
            error_message: Error details

        Returns:
            Database ID of saved generation, or None if save failed
        """
        try:
            # Save model info as "BackendName:model_id" for better tracking
            model_info = f"{self.backend.__class__.__name__}:{self.backend.model_id}"

            return self.database.save_generation(
                schema=schema,
                model_backend=model_info,
                num_records=num_records,
                data=None,
                success=False,
                error_message=error_message
            )
        except Exception as e:
            logger.error(f"Failed to save failed generation: {e}", exc_info=True)
            return None

    def get_history(
        self,
        limit: int = 10,
        success_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve generation history from database.

        Args:
            limit: Maximum number of generations to return
            success_only: If True, only return successful generations

        Returns:
            List of generation dictionaries

        Example:
            >>> history = service.get_history(limit=5, success_only=True)
            >>> for gen in history:
            ...     print(f"{gen['id']}: {gen['num_records']} records")
        """
        if not self.database:
            logger.warning("No database configured, cannot retrieve history")
            return []

        generations = self.database.get_recent_generations(
            limit=limit,
            backend=None,  # All backends
            success_only=success_only
        )

        return [gen.to_dict() for gen in generations]

    def get_generation(self, generation_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific generation by ID.

        Args:
            generation_id: Database ID of the generation

        Returns:
            Generation dictionary or None if not found
        """
        if not self.database:
            logger.warning("No database configured")
            return None

        generation = self.database.get_generation(generation_id)
        return generation.to_dict() if generation else None

    def close(self) -> None:
        """
        Clean up resources.

        Call this when done using the service to close database connections.

        Example:
            >>> service = GeneratorService(backend, db)
            >>> try:
            ...     result = service.generate(schema, 10)
            ... finally:
            ...     service.close()

        Or use as context manager:
            >>> with service:
            ...     result = service.generate(schema, 10)
        """
        # FIX: Only close database if we created it
        if self.database and self._owns_database:
            self.database.close()
            logger.debug("GeneratorService closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
