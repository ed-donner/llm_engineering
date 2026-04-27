"""Ollama client shim compatible with the local client.py interface."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from dotenv import find_dotenv, load_dotenv


class LLMError(RuntimeError):
    """Raised when the model client cannot be configured or called."""


def log_debug(message: str, *, flag: bool = False, tag: str = "LLM_DEBUG") -> None:
    """Standalone debug logger controlled by flag/env variable."""
    enabled = flag or os.getenv("LLM_AGENT_DEBUG", "false").lower() in {"1", "true", "yes"}
    if enabled:
        print(f"[{tag}] {message}", flush=True)


@dataclass
class _OllamaOutputText:
    """Mimic the small response shape expected by existing callers."""

    text: str


@dataclass
class _OllamaOutputItem:
    """Wrap text in a content list so callers can inspect response.output if needed."""

    content: list[_OllamaOutputText]


class _OllamaResponse:
    """Minimal response object shaped like the OpenAI Responses client output."""

    def __init__(self, text: str, raw: dict[str, Any]) -> None:
        self.output_text = text
        self.output = [_OllamaOutputItem(content=[_OllamaOutputText(text=text)])]
        self.raw = raw


def _normalize_base_url(raw_base_url: str | None) -> str:
    """Normalize env-provided base URLs so they point at the Ollama server root."""
    base_url = (raw_base_url or "http://127.0.0.1:11434").rstrip("/")
    if base_url.endswith("/api"):
        base_url = base_url[: -len("/api")]
    if base_url.endswith("/v1"):
        base_url = base_url[: -len("/v1")]
    return base_url


def _content_to_text(content: Any) -> str:
    """Convert OpenAI-style content blocks or plain strings into one prompt string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(str(text))
            elif item is not None:
                parts.append(str(item))
        return "\n".join(part for part in parts if part).strip()
    if isinstance(content, dict):
        text = content.get("text")
        return str(text).strip() if text else ""
    return str(content).strip()


def _to_ollama_messages(input_payload: Any) -> list[dict[str, str]]:
    """Translate the existing input payload shape into Ollama chat messages."""
    if isinstance(input_payload, str):
        return [{"role": "user", "content": input_payload}]

    messages: list[dict[str, str]] = []
    if not isinstance(input_payload, list):
        raise LLMError("Unsupported input payload for Ollama client.")

    for item in input_payload:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "user"))
        content_text = _content_to_text(item.get("content", ""))
        if content_text:
            messages.append({"role": role, "content": content_text})

    if not messages:
        raise LLMError("No usable messages were found in the input payload.")
    return messages


class _OllamaResponsesAPI:
    """Implement a `.responses.create(...)` method so import swaps stay minimal."""

    def __init__(self, *, base_url: str, http_client: httpx.Client) -> None:
        self.base_url = base_url
        self.http_client = http_client

    def create(
        self,
        *,
        model: str,
        input: Any,
        user: str | None = None,
        timeout: int = 180,
        tools: list[dict[str, Any]] | None = None,
        **_: Any,
    ) -> _OllamaResponse:
        messages = _to_ollama_messages(input)
        if tools:
            log_debug(
                "Ollama shim received tool specs; native tool calling is ignored in this adapter.",
                tag="OLLAMA_CLIENT",
            )

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        headers = {"Content-Type": "application/json"}
        if user:
            headers["X-Request-User"] = str(user)

        try:
            response = self.http_client.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers=headers,
                timeout=float(timeout),
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(f"Ollama request failed: {exc}") from exc

        raw = response.json()
        message = raw.get("message") or {}
        text = str(message.get("content", "")).strip()
        if not text:
            raise LLMError("Ollama returned an empty response.")
        return _OllamaResponse(text=text, raw=raw)


class _OllamaClient:
    """Container that exposes `.responses.create(...)` like the OpenAI client."""

    def __init__(self, *, base_url: str, http_client: httpx.Client) -> None:
        self.responses = _OllamaResponsesAPI(base_url=base_url, http_client=http_client)


def load_client() -> tuple[Any, str, str]:
    """Create an Ollama-backed client and resolve model/user context."""
    dotenv_path = find_dotenv(filename=".env", usecwd=True) or find_dotenv(filename="env", usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path=dotenv_path, override=False)
    else:
        local_env = Path(__file__).resolve().parent / ".env"
        if not local_env.exists():
            local_env = Path(__file__).resolve().parent / "env"
        if local_env.exists():
            load_dotenv(dotenv_path=local_env, override=False)

    username = os.getenv("OLLAMA_USERNAME") or os.getenv("OPENAI_USERNAME") or "user@example.com"
    request_user = os.getenv("OLLAMA_USER") or os.getenv("OPENAI_USER") or username.split("@", 1)[0]

    base_url = _normalize_base_url(os.getenv("OLLAMA_BASE_URL") or os.getenv("OPENAI_BASE_URL"))
    model_name = os.getenv("OLLAMA_MODEL") or os.getenv("OPENAI_MODEL") or "llama3.1:8b"

    allow_insecure_ssl = os.getenv("OLLAMA_ALLOW_INSECURE_SSL", "false").lower() in {
        "1",
        "true",
        "yes",
    }
    ca_bundle = (
        os.getenv("OLLAMA_CA_BUNDLE")
        or os.getenv("SSL_CERT_FILE")
        or os.getenv("REQUESTS_CA_BUNDLE")
    )

    verify: bool | str = True
    if allow_insecure_ssl:
        verify = False
    elif ca_bundle:
        if not os.path.exists(ca_bundle):
            raise LLMError(f"CA bundle file not found: {ca_bundle}")
        verify = ca_bundle

    http_client = httpx.Client(verify=verify, timeout=180.0)
    return _OllamaClient(base_url=base_url, http_client=http_client), model_name, request_user


def create_response(
    *,
    client: Any,
    model_name: str,
    request_user: str,
    conversation: list[dict[str, Any]],
    debug: bool,
    purpose: str,
    tools: list[dict[str, Any]],
    timeout: int,
) -> Any:
    """Compatibility wrapper mirroring the existing client.py helper."""
    log_debug(f"tool_called=ollama.api.chat purpose={purpose}", flag=debug, tag="OLLAMA_CLIENT")
    return client.responses.create(
        model=model_name,
        input=conversation,
        tools=tools,
        user=str(request_user),
        timeout=timeout,
    )
