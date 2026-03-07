"""
RAG retriever: embed product summaries, index train items, retrieve top-k similar for a query.
Used to build "Similar products: ..." context for the pricer prompt.
"""
from __future__ import annotations

import numpy as np
from typing import List, Optional

# Lazy init of embedding model to avoid loading until needed
_embedding_model = None
_embedding_name = "sentence-transformers/all-MiniLM-L6-v2"


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer(_embedding_name)
        except Exception as e:
            raise RuntimeError(
                f"Install sentence-transformers: pip install sentence-transformers. Error: {e}"
            ) from e
    return _embedding_model


def embed_texts(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """Embed a list of strings. Returns list of vectors."""
    model = _get_embedding_model()
    return model.encode(texts, batch_size=batch_size, show_progress_bar=len(texts) > 50).tolist()


class RAGIndex:
    """In-memory index of items by summary embedding. Retrieve top-k by similarity."""

    def __init__(self, items: list, text_fn=None):
        """
        items: list of objects with .summary (and optionally .title, .price).
        text_fn: optional callable(item) -> str for index text; default is item.summary or title.
        """
        self.items = items
        self.text_fn = text_fn or (lambda i: (i.summary or "") if hasattr(i, "summary") else str(i))
        self.texts = [self.text_fn(i) for i in items]
        self.embeddings = embed_texts(self.texts)
        self._emb = np.array(self.embeddings, dtype="float32")

    def retrieve(self, query: str, k: int = 5) -> List[tuple]:
        """
        query: product summary (or description) to find similar items for.
        k: number of nearest items to return.
        Returns list of (item, score) where score is negative L2 distance (higher = more similar).
        """
        model = _get_embedding_model()
        q = model.encode([query], show_progress_bar=False)
        q = np.array(q, dtype="float32")
        # L2 distances
        dists = np.linalg.norm(self._emb - q, axis=1)
        # Negative distance so higher = better
        scores = -dists
        top_idx = np.argsort(scores)[::-1][:k]
        return [(self.items[i], float(scores[i])) for i in top_idx]

    def format_similar_products(self, query: str, k: int = 5) -> str:
        """
        Retrieve top-k and format as a string for the prompt, e.g.:
        Similar products: "Title A" $45; "Title B" $52
        """
        pairs = self.retrieve(query, k=k)
        parts = []
        for item, _ in pairs:
            title = getattr(item, "title", "Product") or "Product"
            price = getattr(item, "price", 0)
            parts.append(f'"{title[:50]}" ${price:.0f}')
        return "Similar products: " + "; ".join(parts) if parts else "Similar products: (none)"


def build_rag_index_from_items(train_items: list, text_fn=None) -> RAGIndex:
    """Build a RAGIndex from a list of Items (e.g. train set)."""
    return RAGIndex(train_items, text_fn=text_fn)
