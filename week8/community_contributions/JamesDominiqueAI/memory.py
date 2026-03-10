"""
memory.py
---------
Vector-memory layer backed by ChromaDB + sentence-transformers.

The agent stores every retrieved text chunk here so it can later call
`retrieve()` to surface the most relevant passages when drafting its report.
This implements the RAG (Retrieval-Augmented Generation) pattern.
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


# ── Optional imports with graceful degradation ────────────────────────────────
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("chromadb not installed — memory disabled (pip install chromadb)")

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False
    logger.warning("sentence-transformers not installed — memory disabled")


# ── Memory Store ──────────────────────────────────────────────────────────────

class ResearchMemory:
    """
    Persistent vector store for research documents.

    Lifecycle:
        mem = ResearchMemory(config)
        mem.store("Some article text …", metadata={"source": "Reuters"})
        chunks = mem.retrieve("causes of fuel shortage")
    """

    def __init__(self, config):
        self._config = config
        self._ready = False
        self._collection = None
        self._ef = None
        self._doc_count = 0

        if CHROMA_AVAILABLE and ST_AVAILABLE:
            self._init_chroma()
        else:
            logger.warning("Memory store disabled: missing dependencies.")

    # ── Initialisation ────────────────────────────────────────────────────────

    def _init_chroma(self) -> None:
        try:
            self._ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self._config.embedding_model
            )
            client = chromadb.PersistentClient(path=self._config.chroma_persist_dir)
            self._collection = client.get_or_create_collection(
                name=self._config.collection_name,
                embedding_function=self._ef,
            )
            self._doc_count = self._collection.count()
            self._ready = True
            logger.info(
                "ChromaDB ready — collection '%s', %d existing docs.",
                self._config.collection_name,
                self._doc_count,
            )
        except Exception as exc:
            logger.error("ChromaDB init failed: %s", exc)
            self._ready = False

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def is_ready(self) -> bool:
        return self._ready

    @property
    def document_count(self) -> int:
        if self._ready and self._collection:
            return self._collection.count()
        return 0

    def store(
        self,
        text: str,
        metadata: Optional[dict] = None,
        chunk_size: int = 800,
        overlap: int = 100,
    ) -> int:
        """
        Chunk `text` and add to the vector store.
        Returns the number of chunks stored.
        """
        if not self._ready or not text.strip():
            return 0

        chunks = self._chunk_text(text, chunk_size, overlap)
        if not chunks:
            return 0

        ids, docs, metas = [], [], []
        ts = str(int(time.time() * 1000))

        for i, chunk in enumerate(chunks):
            uid = hashlib.md5(f"{ts}-{i}-{chunk[:40]}".encode()).hexdigest()
            ids.append(uid)
            docs.append(chunk)
            metas.append({**(metadata or {}), "chunk_index": i, "timestamp": ts})

        try:
            self._collection.add(documents=docs, ids=ids, metadatas=metas)
            logger.debug("Stored %d chunks in memory.", len(chunks))
            return len(chunks)
        except Exception as exc:
            logger.error("Memory store failed: %s", exc)
            return 0

    def retrieve(self, query: str, top_k: Optional[int] = None) -> list[dict]:
        """
        Return the top-k most similar chunks for `query`.

        Each result dict has keys: text, source, distance.
        """
        if not self._ready or not query.strip():
            return []

        k = top_k or self._config.top_k_retrieval

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(k, self._collection.count() or 1),
                include=["documents", "metadatas", "distances"],
            )
            output = []
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                output.append(
                    {
                        "text": doc,
                        "source": meta.get("source", "unknown"),
                        "distance": round(dist, 4),
                    }
                )
            return output
        except Exception as exc:
            logger.error("Memory retrieval failed: %s", exc)
            return []

    def clear(self) -> None:
        """Wipe the collection (useful between research sessions)."""
        if self._ready and self._collection:
            try:
                client = self._collection._client
                client.delete_collection(self._config.collection_name)
                self._init_chroma()
                logger.info("Memory cleared.")
            except Exception as exc:
                logger.error("Memory clear failed: %s", exc)

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _chunk_text(text: str, size: int, overlap: int) -> list[str]:
        """Sliding-window character chunker."""
        text = text.strip()
        if len(text) <= size:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            chunks.append(text[start:end])
            if end == len(text):
                break
            start += size - overlap
        return chunks
