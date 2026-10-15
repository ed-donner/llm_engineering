"""Ollama local server, list models and stream via OpenAI-compatible /v1 API."""

from __future__ import annotations

from typing import Any

import requests
from openai import OpenAI

from openai_llm import stream_chat_completions

DEFAULT_OLLAMA_HOST = "http://localhost:11434"


def openai_compatible_base_url(host: str) -> str:
    return f"{host.rstrip('/')}/v1"


def make_ollama_client(host: str = DEFAULT_OLLAMA_HOST) -> OpenAI:
    """OpenAI SDK client pointed at Ollama's local OpenAI-compatible endpoint."""
    return OpenAI(base_url=openai_compatible_base_url(host), api_key="ollama")


def fetch_installed_model_names(
    host: str = DEFAULT_OLLAMA_HOST,
    *,
    timeout: float = 10,
) -> list[str]:
    """Model names Ollama has locally (same as `ollama list`)."""
    r = requests.get(f"{host.rstrip('/')}/api/tags", timeout=timeout)
    r.raise_for_status()
    return [m["name"] for m in r.json().get("models", [])]


def stream_ollama_chat(
    client: OpenAI,
    model: str,
    messages: list[dict[str, Any]],
) -> Any:
    """Stream a chat completion through the local Ollama OpenAI-compatible API."""
    return stream_chat_completions(client, model, messages)
