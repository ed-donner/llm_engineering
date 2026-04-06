"""
Abstract base class for LLM backend implementations.

This module provides the interface that all backend implementations must follow,
enabling swappable model providers (Strategy Pattern).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class GenerationParams:
    """Parameters for data generation."""
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls."""
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }


@dataclass
class GenerationResult:
    """Result from data generation."""
    data: List[Dict[str, Any]]
    raw_response: str
    num_records: int
    success: bool
    error_message: Optional[str] = None


class ModelBackend(ABC):
    """
    Abstract base class for LLM backend implementations.

    Provides interface for generating synthetic data using various
    LLM providers. Subclasses must implement generate() method.

    Attributes:
        api_key: Optional API key for cloud providers
        model_id: Identifier for the specific model to use
        base_url: Base URL for API endpoint
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: str = "meta-llama/Llama-3.2-3B-Instruct",
        base_url: str = "https://router.huggingface.co/v1/"
    ):
        """
        Initialize backend.

        Args:
            api_key: API key for authentication (optional for local models)
            model_id: Model identifier
            base_url: API endpoint base URL
        """
        self.api_key = api_key
        self.model_id = model_id
        self.base_url = base_url

    @abstractmethod
    def generate(
        self,
        schema: Dict[str, Any],
        num_records: int,
        params: Optional[GenerationParams] = None
    ) -> GenerationResult:
        """
        Generate synthetic data based on schema.

        Args:
            schema: JSON schema defining the data structure
            num_records: Number of records to generate
            params: Generation parameters (temperature, etc.)

        Returns:
            GenerationResult containing the generated data

        Raises:
            APIKeyError: If API key is required but not provided
            BackendError: If generation fails
        """
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Validate that the backend can connect and authenticate.

        Returns:
            True if connection is valid, False otherwise
        """
        pass

    def _build_prompt(self, schema: Dict[str, Any], num_records: int) -> str:
        """
        Build generation prompt from schema.

        Args:
            schema: JSON schema
            num_records: Number of records to generate

        Returns:
            Formatted prompt string
        """
        schema_desc = self._format_schema(schema)

        prompt = f"""Generate {num_records} synthetic data records based on the following schema.

Schema:
{schema_desc}

Requirements:
- Generate exactly {num_records} records
- Return ONLY a valid JSON array of objects
- Each object must match the schema exactly
- Ensure data is realistic and diverse
- No additional text or explanation

Output format:
[
  {{"field1": "value1", "field2": "value2"}},
  {{"field1": "value1", "field2": "value2"}}
]"""

        return prompt

    def _format_schema(self, schema: Dict[str, Any]) -> str:
        """
        Format schema for prompt.

        Args:
            schema: JSON schema

        Returns:
            Formatted schema string
        """
        lines = []
        for field, spec in schema.items():
            if isinstance(spec, dict):
                field_type = spec.get("type", "string")
                description = spec.get("description", "")
                lines.append(f"  - {field} ({field_type}): {description}")
            else:
                lines.append(f"  - {field}: {spec}")

        return "\n".join(lines)
