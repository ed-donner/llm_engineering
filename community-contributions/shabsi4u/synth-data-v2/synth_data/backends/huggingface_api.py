"""
HuggingFace Inference API backend implementation.

Uses the HuggingFace Inference API with OpenAI-compatible client
for generating synthetic data.
"""

import json
import logging
from typing import Dict, Any, List, Optional

from openai import OpenAI

from .base import ModelBackend, GenerationParams, GenerationResult
from ..exceptions import APIKeyError, BackendError

logger = logging.getLogger(__name__)


class HuggingFaceAPIBackend(ModelBackend):
    """
    Backend for HuggingFace Inference API.

    Uses OpenAI-compatible client to interact with HuggingFace models.
    Supports free tier with rate limiting considerations.

    Example:
        >>> backend = HuggingFaceAPIBackend(api_key="hf_xxx")
        >>> schema = {"name": {"type": "string"}, "age": {"type": "integer"}}
        >>> result = backend.generate(schema, num_records=10)
        >>> print(len(result.data))
        10
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: str = "meta-llama/Llama-3.2-3B-Instruct",
        base_url: str = "https://api-inference.huggingface.co/v1/"
    ):
        """
        Initialize HuggingFace API backend.

        Args:
            api_key: HuggingFace API key (starts with 'hf_')
            model_id: Model to use (default: Llama 3.2 3B)
            base_url: HuggingFace Inference API endpoint
        """
        super().__init__(api_key=api_key, model_id=model_id, base_url=base_url)
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        """
        Get or create OpenAI client for HuggingFace API.

        Returns:
            Configured OpenAI client

        Raises:
            APIKeyError: If API key is not provided
        """
        if not self.api_key:
            raise APIKeyError(
                "HuggingFace API key required. "
                "Provide via api_key parameter or HUGGINGFACE_API_KEY env variable."
            )

        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            logger.info(f"Initialized HuggingFace client with model: {self.model_id}")

        return self._client

    def validate_connection(self) -> bool:
        """
        Validate API key and connection.

        Returns:
            True if connection is valid, False otherwise
        """
        if not self.api_key:
            return False

        try:
            client = self._get_client()
            # Try a minimal API call to test connection
            response = client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return response is not None
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False

    def generate(
        self,
        schema: Dict[str, Any],
        num_records: int,
        params: Optional[GenerationParams] = None
    ) -> GenerationResult:
        """
        Generate synthetic data using HuggingFace API.

        Args:
            schema: JSON schema defining data structure
            num_records: Number of records to generate
            params: Generation parameters (temperature, max_tokens, etc.)

        Returns:
            GenerationResult with parsed data

        Raises:
            APIKeyError: If API key is missing
            BackendError: If generation or parsing fails
        """
        if params is None:
            params = GenerationParams()

        logger.info(
            f"Generating {num_records} records using {self.model_id}"
        )

        # Build prompt
        prompt = self._build_prompt(schema, num_records)
        logger.debug(f"Generated prompt: {prompt[:200]}...")

        # FIX: Initialize raw_response for error handling
        raw_response = ""

        try:
            # Call API
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a synthetic data generator. "
                                   "Generate realistic, diverse data that matches "
                                   "the provided schema. Return only valid JSON arrays."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=params.temperature,
                max_tokens=params.max_tokens,
                top_p=params.top_p
            )

            # Extract response
            raw_response = response.choices[0].message.content
            logger.debug(f"Raw response: {raw_response[:200]}...")

            # Parse JSON
            data = self._parse_response(raw_response)

            # Validate record count
            if len(data) != num_records:
                logger.warning(
                    f"Generated {len(data)} records, expected {num_records}"
                )

            logger.info(f"Successfully generated {len(data)} records")

            return GenerationResult(
                data=data,
                raw_response=raw_response,
                num_records=len(data),
                success=True
            )

        except APIKeyError:
            raise
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON response: {e}"
            logger.error(error_msg)
            # FIX: raw_response is now always initialized
            return GenerationResult(
                data=[],
                raw_response=raw_response,
                num_records=0,
                success=False,
                error_message=error_msg
            )
        except Exception as e:
            error_msg = f"Generation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise BackendError(error_msg) from e

    def _parse_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse JSON response from LLM.

        Handles common formatting issues like markdown code blocks,
        extra whitespace, and text before/after JSON.

        Args:
            response: Raw response string

        Returns:
            Parsed list of dictionaries

        Raises:
            json.JSONDecodeError: If parsing fails
        """
        # Clean response
        response = response.strip()

        # Remove markdown code blocks
        if response.startswith("```"):
            # Remove opening ```json or ```
            lines = response.split("\n")
            lines = lines[1:]  # Remove first line with ```
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]  # Remove last line with ```
            response = "\n".join(lines).strip()

        # Try to find JSON array in response
        start_idx = response.find("[")
        end_idx = response.rfind("]")

        if start_idx != -1 and end_idx != -1:
            response = response[start_idx:end_idx + 1]

        # Parse JSON
        data = json.loads(response)

        if not isinstance(data, list):
            raise ValueError("Response is not a JSON array")

        return data
