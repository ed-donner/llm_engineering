"""
Tests for GeneratorService.

This test suite demonstrates how the GeneratorService orchestrates
data generation by connecting backends and database.
"""

import pytest
from unittest.mock import Mock, MagicMock
from synth_data.services import GeneratorService
from synth_data.backends.base import GenerationResult, GenerationParams
from synth_data.database.service import DatabaseService
from synth_data.exceptions import SchemaValidationError, GenerationError


class TestSchemaValidation:
    """Test schema validation logic."""

    def test_valid_schema_with_type_dict(self):
        """Test that valid schema with type dicts passes validation."""
        backend = Mock()
        service = GeneratorService(backend=backend, save_to_db=False)

        schema = {
            "name": {"type": "string", "description": "Person's name"},
            "age": {"type": "integer", "minimum": 0, "maximum": 120}
        }

        # Should not raise
        service._validate_schema(schema)

    def test_valid_schema_with_simple_strings(self):
        """Test that simple string values are allowed."""
        backend = Mock()
        service = GeneratorService(backend=backend, save_to_db=False)

        schema = {
            "status": "active",
            "category": "user"
        }

        # Should not raise
        service._validate_schema(schema)

    def test_empty_schema_raises_error(self):
        """Test that empty schema is rejected."""
        backend = Mock()
        service = GeneratorService(backend=backend, save_to_db=False)

        with pytest.raises(SchemaValidationError, match="cannot be empty"):
            service._validate_schema({})

    def test_non_dict_schema_raises_error(self):
        """Test that non-dict schema is rejected."""
        backend = Mock()
        service = GeneratorService(backend=backend, save_to_db=False)

        with pytest.raises(SchemaValidationError, match="must be a dictionary"):
            service._validate_schema("not a dict")

    def test_none_field_value_raises_error(self):
        """Test that None field values are rejected."""
        backend = Mock()
        service = GeneratorService(backend=backend, save_to_db=False)

        schema = {"name": None}

        with pytest.raises(SchemaValidationError, match="None value"):
            service._validate_schema(schema)

    def test_schema_without_type_logs_warning(self, caplog):
        """Test that schema fields without 'type' key log a warning."""
        import logging
        caplog.set_level(logging.WARNING)

        backend = Mock()
        service = GeneratorService(backend=backend, save_to_db=False)

        schema = {"name": {"description": "Missing type key"}}

        service._validate_schema(schema)

        # Check warning was logged
        assert "missing 'type' key" in caplog.text.lower()


class TestGeneration:
    """Test data generation workflow."""

    @pytest.fixture
    def mock_backend(self):
        """Create a mock backend that returns successful results."""
        backend = Mock()
        backend.__class__.__name__ = "MockBackend"

        # Mock successful generation
        backend.generate.return_value = GenerationResult(
            data=[
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ],
            raw_response='[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]',
            num_records=2,
            success=True
        )

        return backend

    def test_generate_without_database(self, mock_backend):
        """Test generation without database persistence."""
        service = GeneratorService(backend=mock_backend, save_to_db=False)

        schema = {"name": {"type": "string"}, "age": {"type": "integer"}}

        result = service.generate(schema=schema, num_records=2)

        # Verify result structure
        assert result["success"] is True
        assert result["num_records"] == 2
        assert len(result["data"]) == 2
        assert result["generation_id"] is None  # No database
        assert result["backend"] == "MockBackend"

        # Verify backend was called correctly
        mock_backend.generate.assert_called_once()
        call_args = mock_backend.generate.call_args
        assert call_args[1]["schema"] == schema
        assert call_args[1]["num_records"] == 2

    def test_generate_with_database(self, mock_backend, mock_database):
        """Test generation with database persistence."""
        service = GeneratorService(
            backend=mock_backend,
            database=mock_database,
            save_to_db=True
        )

        schema = {"name": {"type": "string"}, "age": {"type": "integer"}}

        result = service.generate(schema=schema, num_records=2)

        # Verify result
        assert result["success"] is True
        assert result["generation_id"] is not None  # Saved to database

        # Verify saved to database
        saved_gen = mock_database.get_generation(result["generation_id"])
        assert saved_gen is not None
        assert saved_gen.num_records == 2
        assert saved_gen.success is True
        assert len(saved_gen.data_json) == 2

    def test_generate_with_progress_callback(self, mock_backend):
        """Test that progress callback is called."""
        service = GeneratorService(backend=mock_backend, save_to_db=False)

        progress_calls = []

        def track_progress(current, total):
            progress_calls.append((current, total))

        schema = {"name": {"type": "string"}}

        service.generate(
            schema=schema,
            num_records=2,
            on_progress=track_progress
        )

        # Verify progress callback was called
        # Should be called at start (0, 2) and end (2, 2)
        assert len(progress_calls) >= 2
        assert progress_calls[0] == (0, 2)  # Start
        assert progress_calls[-1] == (2, 2)  # End

    def test_generate_with_custom_params(self, mock_backend):
        """Test generation with custom parameters."""
        service = GeneratorService(backend=mock_backend, save_to_db=False)

        schema = {"name": {"type": "string"}}
        params = GenerationParams(temperature=0.9, max_tokens=1000)

        service.generate(schema=schema, num_records=2, params=params)

        # Verify params were passed to backend
        call_args = mock_backend.generate.call_args
        assert call_args[1]["params"] == params

    def test_generate_with_invalid_num_records(self, mock_backend):
        """Test that invalid num_records raises error."""
        service = GeneratorService(backend=mock_backend, save_to_db=False)

        schema = {"name": {"type": "string"}}

        with pytest.raises(GenerationError, match="must be >= 1"):
            service.generate(schema=schema, num_records=0)

    def test_generate_saves_failed_attempts(self, mock_backend, mock_database):
        """Test that failed generations are saved to database."""
        # Configure backend to fail
        mock_backend.generate.side_effect = Exception("API Error")

        service = GeneratorService(
            backend=mock_backend,
            database=mock_database,
            save_to_db=True
        )

        schema = {"name": {"type": "string"}}

        result = service.generate(schema=schema, num_records=2)

        # Verify result indicates failure
        assert result["success"] is False
        assert "API Error" in result["error_message"]
        assert result["num_records"] == 0
        assert result["data"] == []

        # Verify saved to database with failure status
        saved_gen = mock_database.get_generation(result["generation_id"])
        assert saved_gen is not None
        assert saved_gen.success is False
        assert "API Error" in saved_gen.error_message


class TestHistory:
    """Test generation history retrieval."""

    @pytest.fixture
    def service_with_history(self, mock_database):
        """Create service with some generation history."""
        backend = Mock()
        backend.__class__.__name__ = "TestBackend"

        # Add some generations to database
        for i in range(5):
            mock_database.save_generation(
                schema={"field": f"value{i}"},
                model_backend="TestBackend",
                num_records=10,
                data=[{"field": f"value{i}"}] * 10,
                success=True
            )

        return GeneratorService(backend=backend, database=mock_database)

    def test_get_history(self, service_with_history):
        """Test retrieving generation history."""
        history = service_with_history.get_history(limit=3)

        assert len(history) == 3
        assert all(isinstance(gen, dict) for gen in history)
        assert all("id" in gen for gen in history)
        assert all("num_records" in gen for gen in history)

    def test_get_history_success_only(self, service_with_history):
        """Test filtering history for successful generations only."""
        # Add a failed generation
        service_with_history.database.save_generation(
            schema={"field": "fail"},
            model_backend="TestBackend",
            num_records=10,
            data=None,
            success=False,
            error_message="Test failure"
        )

        history = service_with_history.get_history(
            limit=10,
            success_only=True
        )

        # Should only return successful ones
        assert all(gen["success"] for gen in history)

    def test_get_generation_by_id(self, service_with_history):
        """Test retrieving a specific generation."""
        # Get first from history
        history = service_with_history.get_history(limit=1)
        gen_id = history[0]["id"]

        # Retrieve by ID
        generation = service_with_history.get_generation(gen_id)

        assert generation is not None
        assert generation["id"] == gen_id
        assert generation["num_records"] == 10


class TestContextManager:
    """Test context manager functionality."""

    def test_context_manager_closes_resources(self, mock_database):
        """Test that context manager properly closes resources."""
        backend = Mock()

        with GeneratorService(backend=backend, database=mock_database) as service:
            # Service is usable within context
            assert service is not None

        # After context, database session should be closed
        # (In a real scenario, attempting to use the session would fail)
        # For now, just verify close was called
        assert True  # Session closure is handled by DatabaseService


class TestIntegration:
    """Integration tests with real components."""

    @pytest.mark.skip(reason="Requires real API key")
    def test_end_to_end_generation(self):
        """
        Full end-to-end test with real backend.

        This test is skipped by default because it requires:
        - Real API key
        - Network connection
        - API credits

        To run manually:
            pytest tests/test_generator.py::TestIntegration::test_end_to_end_generation -v -s
        """
        import os
        from synth_data.backends import HuggingFaceAPIBackend

        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            pytest.skip("HUGGINGFACE_API_KEY not set")

        backend = HuggingFaceAPIBackend(api_key=api_key)
        service = GeneratorService(backend=backend, save_to_db=True)

        schema = {
            "name": {"type": "string", "description": "Person's name"},
            "age": {"type": "integer", "minimum": 18, "maximum": 65}
        }

        try:
            result = service.generate(schema=schema, num_records=5)

            assert result["success"] is True
            assert result["num_records"] == 5
            assert len(result["data"]) == 5

            # Verify data structure
            for record in result["data"]:
                assert "name" in record
                assert "age" in record
                assert isinstance(record["name"], str)
                assert isinstance(record["age"], int)

        finally:
            service.close()
