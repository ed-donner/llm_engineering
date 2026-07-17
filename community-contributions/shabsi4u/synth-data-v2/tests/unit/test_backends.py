"""
Unit tests for backend implementations.

Tests the ModelBackend interface and HuggingFaceAPIBackend implementation.
"""

import pytest
from synth_data.backends import (
    HuggingFaceAPIBackend,
    GenerationParams,
    GenerationResult
)
from synth_data.backends.base import ModelBackend
from synth_data.exceptions import APIKeyError


class TestGenerationParams:
    """Test GenerationParams dataclass."""

    def test_default_values(self):
        """Test default parameter values."""
        params = GenerationParams()
        assert params.temperature == 0.7
        assert params.max_tokens == 2048
        assert params.top_p == 1.0

    def test_custom_values(self):
        """Test custom parameter values."""
        params = GenerationParams(
            temperature=0.9,
            max_tokens=1024,
            top_p=0.95
        )
        assert params.temperature == 0.9
        assert params.max_tokens == 1024
        assert params.top_p == 0.95

    def test_to_dict(self):
        """Test conversion to dictionary."""
        params = GenerationParams(temperature=0.8)
        params_dict = params.to_dict()
        assert isinstance(params_dict, dict)
        assert params_dict["temperature"] == 0.8
        assert "max_tokens" in params_dict


class TestGenerationResult:
    """Test GenerationResult dataclass."""

    def test_successful_result(self):
        """Test successful generation result."""
        result = GenerationResult(
            data=[{"name": "John"}],
            raw_response='[{"name": "John"}]',
            num_records=1,
            success=True
        )
        assert result.success is True
        assert result.num_records == 1
        assert len(result.data) == 1
        assert result.error_message is None

    def test_failed_result(self):
        """Test failed generation result."""
        result = GenerationResult(
            data=[],
            raw_response="",
            num_records=0,
            success=False,
            error_message="API error"
        )
        assert result.success is False
        assert result.num_records == 0
        assert result.error_message == "API error"


class TestHuggingFaceBackend:
    """Test HuggingFace API backend."""

    def test_init_with_api_key(self, mock_api_key):
        """Test initialization with API key."""
        backend = HuggingFaceAPIBackend(api_key=mock_api_key)
        assert backend.api_key == mock_api_key
        assert backend.model_id == "meta-llama/Llama-3.2-3B-Instruct"
        assert "huggingface" in backend.base_url

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        backend = HuggingFaceAPIBackend()
        assert backend.api_key is None

    def test_init_custom_model(self, mock_api_key):
        """Test initialization with custom model."""
        custom_model = "meta-llama/Llama-3.1-8B-Instruct"
        backend = HuggingFaceAPIBackend(
            api_key=mock_api_key,
            model_id=custom_model
        )
        assert backend.model_id == custom_model

    def test_get_client_without_api_key_raises(self):
        """Test that _get_client raises error without API key."""
        backend = HuggingFaceAPIBackend()
        with pytest.raises(APIKeyError, match="API key required"):
            backend._get_client()

    def test_get_client_with_api_key(self, mock_api_key):
        """Test that _get_client creates client with API key."""
        backend = HuggingFaceAPIBackend(api_key=mock_api_key)
        client = backend._get_client()
        assert client is not None
        assert client.api_key == mock_api_key

    def test_build_prompt(self, mock_api_key, sample_schema):
        """Test prompt building from schema."""
        backend = HuggingFaceAPIBackend(api_key=mock_api_key)
        prompt = backend._build_prompt(sample_schema, num_records=5)

        assert "5" in prompt
        assert "name" in prompt
        assert "age" in prompt
        assert "email" in prompt
        assert "JSON" in prompt

    def test_format_schema(self, mock_api_key, sample_schema):
        """Test schema formatting."""
        backend = HuggingFaceAPIBackend(api_key=mock_api_key)
        formatted = backend._format_schema(sample_schema)

        assert "name" in formatted
        assert "age" in formatted
        assert "email" in formatted
        assert "string" in formatted
        assert "integer" in formatted

    def test_parse_response_clean_json(
        self,
        mock_api_key,
        sample_json_response
    ):
        """Test parsing clean JSON response."""
        backend = HuggingFaceAPIBackend(api_key=mock_api_key)
        data = backend._parse_response(sample_json_response)

        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "John Doe"

    def test_parse_response_with_markdown(
        self,
        mock_api_key,
        sample_json_with_markdown
    ):
        """Test parsing JSON wrapped in markdown code blocks."""
        backend = HuggingFaceAPIBackend(api_key=mock_api_key)
        data = backend._parse_response(sample_json_with_markdown)

        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "John Doe"

    def test_parse_response_with_extra_text(self, mock_api_key):
        """Test parsing JSON with extra text before/after."""
        response = """Here is the data:
        [{"name": "John", "age": 30}]
        That's all!"""

        backend = HuggingFaceAPIBackend(api_key=mock_api_key)
        data = backend._parse_response(response)

        assert isinstance(data, list)
        assert len(data) == 1

    def test_parse_response_invalid_json(self, mock_api_key):
        """Test parsing invalid JSON raises error."""
        backend = HuggingFaceAPIBackend(api_key=mock_api_key)

        with pytest.raises(Exception):  # JSONDecodeError or ValueError
            backend._parse_response("not valid json")

    def test_validate_connection_without_key(self):
        """Test connection validation without API key."""
        backend = HuggingFaceAPIBackend()
        assert backend.validate_connection() is False

    @pytest.mark.skip(reason="Requires real API key and network access")
    def test_generate_integration(self, sample_schema):
        """Integration test with real API (skip by default)."""
        import os
        api_key = os.getenv("HUGGINGFACE_API_KEY")

        if not api_key:
            pytest.skip("HUGGINGFACE_API_KEY not set")

        backend = HuggingFaceAPIBackend(api_key=api_key)
        params = GenerationParams(max_tokens=512)

        result = backend.generate(
            schema=sample_schema,
            num_records=3,
            params=params
        )

        assert result.success is True
        assert len(result.data) > 0
        assert result.num_records > 0
