"""
Dataset Generator — Week 3 exercise.

Uses the OpenAI Python client (Week 1 pattern) to support multiple providers:
- OpenAI (native)
- OpenRouter (multiple models)
- Ollama (local)
- Google Gemini (OpenAI-compatible endpoint)

User describes the kind of data (e.g. airline, insurance); the LLM returns
structured JSON that is parsed to a DataFrame and can be exported as CSV or JSON.
"""

import os
import json
import time
import tempfile
from datetime import datetime
from typing import Literal, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Provider config (Week 1 day2: same client, different base_url + api_key)
# ---------------------------------------------------------------------------

OPENAI_BASE_URL = None  
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OLLAMA_BASE_URL = "http://localhost:11434/v1"

# Models per provider (user can still type a custom model name if supported)
MODELS_OPENAI = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4.1-mini",
]

MODELS_OPENROUTER = [
    "openai/gpt-4o-mini",
    "anthropic/claude-3-haiku",
    "mistralai/mistral-7b-instruct",
    "meta-llama/llama-3-8b-instruct",
]

MODELS_OLLAMA = [
    "llama3.2:1b",
    "llama3.2",
    "deepseek-r1:1.5b",
]
MODELS_GEMINI = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

Provider = Literal["openai", "openrouter", "ollama", "gemini"]

# Single source of truth for Gradio provider dropdown (order preserved)
PROVIDERS = ["openrouter", "openai", "ollama", "gemini"]

SYSTEM_PROMPT = """
You are a dataset generator.

Return ONLY valid JSON.
No markdown.
No explanations.
No text outside JSON.

Format:
{
  "columns": ["column1", "column2"],
  "rows": [
    ["value1", "value2"]
  ]
}
"""


def _get_client(provider: Provider) -> OpenAI:
    """
    Return an OpenAI-compatible client for the given provider (Week 1 day2 pattern).
    Same client library, different endpoint and key.
    """
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in .env")
        return OpenAI(api_key=api_key, base_url=OPENAI_BASE_URL)

    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not set in .env")
        return OpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": "http://localhost:8888",
                "X-Title": "Dataset Generator",
            },
        )

    if provider == "ollama":
        return OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set in .env (get one at https://aistudio.google.com/api-keys)")
        return OpenAI(base_url=GEMINI_BASE_URL, api_key=api_key)

    raise ValueError(f"Unknown provider: {provider}")


def get_models_for_provider(provider: Provider) -> list[str]:
    """Return the list of model IDs for the provider dropdown."""
    if provider == "openai":
        return MODELS_OPENAI
    if provider == "openrouter":
        return MODELS_OPENROUTER
    if provider == "ollama":
        return MODELS_OLLAMA
    if provider == "gemini":
        return MODELS_GEMINI
    return []


class DatasetGenerator:
    """
    Generates tabular mock/dummy data via an LLM.
    Uses the OpenAI Python client so we can switch providers (OpenAI, OpenRouter, Ollama).
    """

    def __init__(self, provider: Provider = "openrouter", api_key: Optional[str] = None):
        self.provider = provider
        self._api_key_override = api_key
        self._client: Optional[OpenAI] = None

    def _client_or_create(self) -> OpenAI:
        if self._client is None:
            self._client = _get_client(self.provider)
        return self._client

    def set_provider(self, provider: Provider) -> None:
        """Switch provider (e.g. when user changes dropdown); resets client."""
        if provider != self.provider:
            self.provider = provider
            self._client = None

    def _call_llm(
        self, model: str, user_input: str, temperature: float = 0.7
    ) -> Tuple[str, float]:
        """Call the configured provider via OpenAI client; return (content, latency_seconds)."""
        client = self._client_or_create()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]
        start = time.time()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        latency = time.time() - start
        content = (response.choices[0].message.content or "").strip()
        return content, latency

    @staticmethod
    def _clean_response(content: str) -> str:
        return content.replace("```json", "").replace("```", "").strip()

    @staticmethod
    def _parse_to_dataframe(content: str) -> pd.DataFrame:
        data = json.loads(content)
        if "columns" not in data or "rows" not in data:
            raise ValueError("Invalid schema: expected 'columns' and 'rows'.")
        return pd.DataFrame(data["rows"], columns=data["columns"])

    def generate(self, model: str, user_input: str) -> Tuple[pd.DataFrame, float]:
        """
        Generate a dataset from a natural-language description (e.g. airline, insurance).
        Returns (DataFrame, latency_seconds). Retries with lower temperature on parse failure.
        """
        content, latency = self._call_llm(model, user_input, temperature=0.7)
        cleaned = self._clean_response(content)
        try:
            df = self._parse_to_dataframe(cleaned)
        except Exception:
            content, latency = self._call_llm(model, user_input, temperature=0.2)
            cleaned = self._clean_response(content)
            df = self._parse_to_dataframe(cleaned)
        return df, latency

    @staticmethod
    def export(df: pd.DataFrame, export_format: Literal["CSV", "JSON"]) -> str:
        """Write DataFrame to a temp file; return the file path for download."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tmp_dir = tempfile.gettempdir()
        if export_format == "CSV":
            path = os.path.join(tmp_dir, f"dataset_{timestamp}.csv")
            df.to_csv(path, index=False)
        else:
            path = os.path.join(tmp_dir, f"dataset_{timestamp}.json")
            df.to_json(path, orient="records", indent=2)
        return path
