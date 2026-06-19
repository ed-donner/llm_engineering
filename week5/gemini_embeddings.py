"""LangChain-compatible embeddings for Google Gemini Embedding models."""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from langchain_core.embeddings import Embeddings
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, SecretStr, model_validator
from typing_extensions import Self

DEFAULT_MODEL = "models/gemini-embedding-2"
DEFAULT_REQUESTS_PER_MINUTE = 90
SEARCH_QUERY_PREFIX = "task: search result | query: {content}"
DOCUMENT_PREFIX = "title: {title} | text: {content}"


def _normalize_model_name(model: str) -> str:
    if model.startswith("models/"):
        return model
    return f"models/{model}"


def _resolve_api_key(explicit: SecretStr | None) -> str | None:
    if explicit is not None:
        return explicit.get_secret_value()
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


class GeminiEmbeddings(BaseModel, Embeddings):
    """Gemini embedding model integration for LangChain.

    Uses the Google Gen AI SDK (`google-genai`) and reads `GOOGLE_API_KEY`
    (or `GEMINI_API_KEY`) from the environment by default.

    Example:
        ```python
        from gemini_embeddings import GeminiEmbeddings

        embeddings = GeminiEmbeddings(model="models/gemini-embedding-2")
        vector = embeddings.embed_query("What is our refund policy?")
        ```
    """

    model: str = Field(default=DEFAULT_MODEL, alias="model_name")
    api_key: SecretStr | None = Field(default=None, alias="google_api_key")
    output_dimensionality: int | None = None
    chunk_size: int = 50
    requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE
    max_retries: int = 5
    show_progress: bool = False
    query_prefix_template: str = SEARCH_QUERY_PREFIX
    document_prefix_template: str = DOCUMENT_PREFIX
    default_document_title: str = "none"

    client: Any = Field(default=None, exclude=True)
    _last_request_time: float = PrivateAttr(default=0.0)

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        protected_namespaces=(),
    )

    @model_validator(mode="after")
    def validate_environment(self) -> Self:
        api_key = _resolve_api_key(self.api_key)
        if not api_key:
            msg = (
                "Google API key not found. Set GOOGLE_API_KEY or GEMINI_API_KEY "
                "in your environment, or pass api_key to GeminiEmbeddings."
            )
            raise ValueError(msg)
        self.client = genai.Client(api_key=api_key)
        self.model = _normalize_model_name(self.model)
        return self

    def _build_config(self) -> types.EmbedContentConfig | None:
        if self.output_dimensionality is None:
            return None
        return types.EmbedContentConfig(
            output_dimensionality=self.output_dimensionality
        )

    def _format_query(self, text: str) -> str:
        return self.query_prefix_template.format(content=text.replace("\n", " "))

    def _format_document(self, text: str) -> str:
        return self.document_prefix_template.format(
            title=self.default_document_title,
            content=text.replace("\n", " "),
        )

    def _seconds_per_request(self) -> float:
        return 60.0 / self.requests_per_minute

    def _throttle(self, num_requests: int) -> None:
        """Wait so we stay under the Gemini embed_content RPM quota."""
        required_gap = num_requests * self._seconds_per_request()
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < required_gap:
            time.sleep(required_gap - elapsed)

    async def _athrottle(self, num_requests: int) -> None:
        required_gap = num_requests * self._seconds_per_request()
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < required_gap:
            await asyncio.sleep(required_gap - elapsed)

    def _mark_request(self) -> None:
        self._last_request_time = time.monotonic()

    @staticmethod
    def _retry_delay_from_error(exc: genai_errors.ClientError) -> float:
        try:
            details = exc.details.get("error", {}).get("details", [])
            for detail in details:
                if detail.get("@type", "").endswith("RetryInfo"):
                    delay = detail.get("retryDelay", "0s")
                    if isinstance(delay, str) and delay.endswith("s"):
                        return float(delay[:-1]) + 1.0
        except (AttributeError, TypeError, ValueError):
            pass
        return 60.0

    def _call_embed(self, texts: list[str]) -> list[list[float]]:
        for attempt in range(self.max_retries):
            self._throttle(len(texts))
            try:
                response = self.client.models.embed_content(
                    model=self.model,
                    contents=texts,
                    config=self._build_config(),
                )
                self._mark_request()
                return [embedding.values for embedding in response.embeddings]
            except genai_errors.ClientError as exc:
                if exc.code == 429 and attempt < self.max_retries - 1:
                    time.sleep(self._retry_delay_from_error(exc))
                    continue
                raise
        msg = f"Failed to embed after {self.max_retries} retries"
        raise RuntimeError(msg)

    async def _acall_embed(self, texts: list[str]) -> list[list[float]]:
        for attempt in range(self.max_retries):
            await self._athrottle(len(texts))
            try:
                response = await self.client.aio.models.embed_content(
                    model=self.model,
                    contents=texts,
                    config=self._build_config(),
                )
                self._mark_request()
                return [embedding.values for embedding in response.embeddings]
            except genai_errors.ClientError as exc:
                if exc.code == 429 and attempt < self.max_retries - 1:
                    await asyncio.sleep(self._retry_delay_from_error(exc))
                    continue
                raise
        msg = f"Failed to embed after {self.max_retries} retries"
        raise RuntimeError(msg)

    def _batched_embed(self, texts: list[str], *, embed_fn: Any) -> list[list[float]]:
        embeddings: list[list[float]] = []
        batch_starts = range(0, len(texts), self.chunk_size)
        if self.show_progress:
            try:
                from tqdm.auto import tqdm

                batch_starts = tqdm(
                    batch_starts,
                    desc="Embedding",
                    total=(len(texts) + self.chunk_size - 1) // self.chunk_size,
                )
            except ImportError:
                pass

        for start in batch_starts:
            batch = texts[start : start + self.chunk_size]
            embeddings.extend(embed_fn(batch))
        return embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        formatted = [self._format_document(text) for text in texts]
        return self._batched_embed(formatted, embed_fn=self._call_embed)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        formatted = [self._format_document(text) for text in texts]
        embeddings: list[list[float]] = []
        batch_starts = range(0, len(formatted), self.chunk_size)
        for start in batch_starts:
            batch = formatted[start : start + self.chunk_size]
            embeddings.extend(await self._acall_embed(batch))
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        return self._call_embed([self._format_query(text)])[0]

    async def aembed_query(self, text: str) -> list[float]:
        embeddings = await self._acall_embed([self._format_query(text)])
        return embeddings[0]
