"""
Unit tests for database operations.

Tests the DatabaseService and Generation model.
"""

import pytest
from datetime import datetime
from synth_data.database import DatabaseService, Generation


class TestGenerationModel:
    """Test Generation model."""

    def test_generation_creation(self, db_session, sample_schema):
        """Test creating a generation instance."""
        generation = Generation(
            schema_json=sample_schema,
            model_backend="huggingface",
            num_records=10,
            data_json=[{"name": "Alice", "age": 30}],
            success=True
        )

        db_session.add(generation)
        db_session.commit()

        assert generation.id is not None
        assert generation.created_at is not None
        assert generation.schema_json == sample_schema
        assert generation.success is True

    def test_generation_to_dict(self, db_session, sample_schema):
        """Test conversion to dictionary."""
        generation = Generation(
            schema_json=sample_schema,
            model_backend="huggingface",
            num_records=5,
            data_json=[{"name": "Bob"}],
            success=True
        )

        db_session.add(generation)
        db_session.commit()

        result = generation.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == generation.id
        assert result["model_backend"] == "huggingface"
        assert result["num_records"] == 5
        assert result["success"] is True
        assert "created_at" in result

    def test_generation_repr(self, db_session, sample_schema):
        """Test string representation."""
        generation = Generation(
            schema_json=sample_schema,
            model_backend="ollama",
            num_records=20,
            success=False,
            error_message="Test error"
        )

        db_session.add(generation)
        db_session.commit()

        repr_str = repr(generation)
        assert "Generation" in repr_str
        assert "ollama" in repr_str
        assert "20" in repr_str
        assert "failed" in repr_str


class TestDatabaseService:
    """Test DatabaseService operations."""

    def test_save_generation_success(self, db_session, sample_schema):
        """Test saving a successful generation."""
        service = DatabaseService(session=db_session)

        data = [
            {"name": "Alice", "age": 30, "email": "alice@example.com"},
            {"name": "Bob", "age": 25, "email": "bob@example.com"}
        ]

        generation_id = service.save_generation(
            schema=sample_schema,
            model_backend="huggingface",
            num_records=2,
            data=data,
            success=True
        )

        assert generation_id is not None
        assert isinstance(generation_id, int)

        # Verify saved correctly
        generation = db_session.query(Generation).filter_by(
            id=generation_id
        ).first()

        assert generation is not None
        assert generation.num_records == 2
        assert generation.success is True
        assert len(generation.data_json) == 2
        assert generation.error_message is None

    def test_save_generation_failure(self, db_session, sample_schema):
        """Test saving a failed generation."""
        service = DatabaseService(session=db_session)

        generation_id = service.save_generation(
            schema=sample_schema,
            model_backend="huggingface",
            num_records=10,
            data=None,
            success=False,
            error_message="API timeout"
        )

        assert generation_id is not None

        generation = db_session.query(Generation).filter_by(
            id=generation_id
        ).first()

        assert generation.success is False
        assert generation.error_message == "API timeout"
        assert generation.data_json is None

    def test_get_generation(self, db_session, sample_schema):
        """Test retrieving a generation by ID."""
        service = DatabaseService(session=db_session)

        # Save a generation
        generation_id = service.save_generation(
            schema=sample_schema,
            model_backend="ollama",
            num_records=5,
            data=[{"name": "Charlie"}]
        )

        # Retrieve it
        generation = service.get_generation(generation_id)

        assert generation is not None
        assert generation.id == generation_id
        assert generation.model_backend == "ollama"
        assert generation.num_records == 5

    def test_get_generation_not_found(self, db_session):
        """Test retrieving non-existent generation."""
        service = DatabaseService(session=db_session)

        generation = service.get_generation(99999)
        assert generation is None

    def test_get_recent_generations(self, db_session, sample_schema):
        """Test retrieving recent generations."""
        service = DatabaseService(session=db_session)

        # Save multiple generations
        ids = []
        for i in range(5):
            gen_id = service.save_generation(
                schema=sample_schema,
                model_backend="huggingface",
                num_records=i + 1,
                data=[]
            )
            ids.append(gen_id)

        # Retrieve recent (limit 3)
        recent = service.get_recent_generations(limit=3)

        assert len(recent) == 3
        # Should be in descending order by date (newest first)
        assert recent[0].id == ids[-1]  # Most recent
        assert recent[1].id == ids[-2]
        assert recent[2].id == ids[-3]

    def test_get_recent_generations_with_backend_filter(
        self,
        db_session,
        sample_schema
    ):
        """Test filtering recent generations by backend."""
        service = DatabaseService(session=db_session)

        # Save generations with different backends
        service.save_generation(
            schema=sample_schema,
            model_backend="huggingface",
            num_records=10,
            data=[]
        )
        service.save_generation(
            schema=sample_schema,
            model_backend="ollama",
            num_records=20,
            data=[]
        )
        service.save_generation(
            schema=sample_schema,
            model_backend="huggingface",
            num_records=30,
            data=[]
        )

        # Filter by backend
        hf_generations = service.get_recent_generations(backend="huggingface")
        ollama_generations = service.get_recent_generations(backend="ollama")

        assert len(hf_generations) == 2
        assert len(ollama_generations) == 1
        assert all(g.model_backend == "huggingface" for g in hf_generations)

    def test_get_recent_generations_success_only(
        self,
        db_session,
        sample_schema
    ):
        """Test filtering for successful generations only."""
        service = DatabaseService(session=db_session)

        # Save mix of successful and failed
        service.save_generation(
            schema=sample_schema,
            model_backend="huggingface",
            num_records=10,
            data=[],
            success=True
        )
        service.save_generation(
            schema=sample_schema,
            model_backend="huggingface",
            num_records=20,
            data=None,
            success=False,
            error_message="Failed"
        )
        service.save_generation(
            schema=sample_schema,
            model_backend="huggingface",
            num_records=30,
            data=[],
            success=True
        )

        # Get only successful
        successful = service.get_recent_generations(success_only=True)

        assert len(successful) == 2
        assert all(g.success for g in successful)

    def test_get_all_generations(self, db_session, sample_schema):
        """Test retrieving all generations."""
        service = DatabaseService(session=db_session)

        # Save multiple generations
        for i in range(7):
            service.save_generation(
                schema=sample_schema,
                model_backend="huggingface",
                num_records=i + 1,
                data=[]
            )

        all_gens = service.get_all_generations()
        assert len(all_gens) == 7

    def test_delete_generation(self, db_session, sample_schema):
        """Test deleting a generation."""
        service = DatabaseService(session=db_session)

        # Save a generation
        generation_id = service.save_generation(
            schema=sample_schema,
            model_backend="huggingface",
            num_records=10,
            data=[]
        )

        # Delete it
        result = service.delete_generation(generation_id)
        assert result is True

        # Verify deleted
        generation = service.get_generation(generation_id)
        assert generation is None

    def test_delete_generation_not_found(self, db_session):
        """Test deleting non-existent generation."""
        service = DatabaseService(session=db_session)

        result = service.delete_generation(99999)
        assert result is False

    def test_count_generations(self, db_session, sample_schema):
        """Test counting generations."""
        service = DatabaseService(session=db_session)

        # Initially empty
        assert service.count_generations() == 0

        # Add some generations
        for i in range(3):
            service.save_generation(
                schema=sample_schema,
                model_backend="huggingface",
                num_records=i + 1,
                data=[]
            )

        assert service.count_generations() == 3

    def test_count_generations_with_backend_filter(
        self,
        db_session,
        sample_schema
    ):
        """Test counting generations by backend."""
        service = DatabaseService(session=db_session)

        # Add generations with different backends
        service.save_generation(
            schema=sample_schema,
            model_backend="huggingface",
            num_records=10,
            data=[]
        )
        service.save_generation(
            schema=sample_schema,
            model_backend="ollama",
            num_records=20,
            data=[]
        )
        service.save_generation(
            schema=sample_schema,
            model_backend="huggingface",
            num_records=30,
            data=[]
        )

        assert service.count_generations() == 3
        assert service.count_generations(backend="huggingface") == 2
        assert service.count_generations(backend="ollama") == 1

    def test_context_manager(self, sample_schema):
        """Test using DatabaseService as context manager."""
        # Note: Not using db_session fixture here - testing full lifecycle
        with DatabaseService(database_url="sqlite:///:memory:") as service:
            generation_id = service.save_generation(
                schema=sample_schema,
                model_backend="huggingface",
                num_records=5,
                data=[]
            )
            assert generation_id is not None

        # Context manager should have closed the session
        # (No assertion here - just testing it doesn't crash)
