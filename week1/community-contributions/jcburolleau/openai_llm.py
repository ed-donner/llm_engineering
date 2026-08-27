"""OpenAI Chat Completions (cloud), streaming entrypoint."""

from typing import Any


def stream_chat_completions(client: Any, model: str, messages: list[dict[str, Any]]) -> Any:
    """Return a streaming chat completion iterator (OpenAI SDK)."""
    return client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )
