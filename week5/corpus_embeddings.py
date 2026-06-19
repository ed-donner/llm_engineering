"""LangChain-compatible embeddings for the Corpus local embedding API."""

from __future__ import annotations

import os
from typing import Any

import httpx
import openai
from langchain_core.embeddings import Embeddings
from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator
from typing_extensions import Self

DEFAULT_MODEL = "text-embedding-nomic-embed-text-v1"
DEFAULT_BASE_URL = "https://booking.offsec.lab/v1"


def _resolve_api_key(explicit: SecretStr | None) -> str | None:
    if explicit is not None:
        return explicit.get_secret_value()
    return os.getenv("CORPUS_LLM_TOKEN")


class CorpusEmbeddings(BaseModel, Embeddings):
    """OpenAI-compatible embedding client for the Corpus local LLM service.

    Reads `CORPUS_LLM_TOKEN` from the environment by default.

    Example:
        ```python
        from corpus_embeddings import CorpusEmbeddings

        embeddings = CorpusEmbeddings(model="text-embedding-nomic-embed-text-v1")
        vector = embeddings.embed_query("What is our refund policy?")
        ```
    """

    model: str = Field(default=DEFAULT_MODEL, alias="model_name")
    base_url: str = DEFAULT_BASE_URL
    api_key: SecretStr | None = Field(default=None, alias="corpus_llm_token")
    chunk_size: int = 100
    show_progress: bool = False
    verify_ssl: bool = False
    max_retries: int = 2

    client: Any = Field(default=None, exclude=True)

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
                "Corpus API token not found. Set CORPUS_LLM_TOKEN in your "
                "environment, or pass api_key to CorpusEmbeddings."
            )
            raise ValueError(msg)

        client_params = {
            "base_url": self.base_url,
            "api_key": api_key,
            "max_retries": self.max_retries,
        }
        http_client = httpx.Client(verify=self.verify_ssl)
        self.client = openai.OpenAI(
            **client_params,
            http_client=http_client,
        ).embeddings
        return self

    @staticmethod
    def _normalize_texts(texts: list[str]) -> list[str]:
        return [text.replace("\n", " ") for text in texts]

    @staticmethod
    def _extract_embeddings(response: openai.types.CreateEmbeddingResponse) -> list[list[float]]:
        return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]

    def _call_embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.create(
            model=self.model,
            input=self._normalize_texts(texts),
        )
        return self._extract_embeddings(response)

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
        return self._batched_embed(texts, embed_fn=self._call_embed)

    def embed_query(self, text: str) -> list[float]:
        return self._call_embed([text])[0]
