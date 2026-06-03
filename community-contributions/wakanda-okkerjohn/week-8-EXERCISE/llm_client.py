"""OpenRouter LLM client – single place for API base URL and key."""
from openai import OpenAI

from config import OPENROUTER_BASE_URL, OPENROUTER_API_KEY, OPENROUTER_MODEL


def get_client() -> OpenAI:
    """Return an OpenAI-compatible client configured for OpenRouter."""
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)


def get_model() -> str:
    """Return the OpenRouter model id to use (e.g. openai/gpt-4o-mini)."""
    return OPENROUTER_MODEL
