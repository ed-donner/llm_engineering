# base_retrieval.py
"""
retrieval/base_retrieval.py — Core retrieval using ChromaDB + OpenAI embeddings.

Key features:
- Dual retrieval: queries on both original and rewritten question, then merges
- LLM reranker: asks the LLM to rank chunks by relevance (RankOrder structured output)
- Metadata filters: year, regulation ID, doc type narrowing
- Retry on all LLM/API calls via tenacity
"""

import os
import sys
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from chromadb import PersistentClient
from tenacity import retry, wait_exponential

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    EMBEDDING_MODEL, COLLECTION_NAME, OPENAI_API_KEY, CHROMA_DB_DIR,
    MODEL, RETRIEVAL_K, FINAL_K, RETRY_MIN_WAIT, RETRY_MAX_WAIT,
)
from retrieval.metadata_filters import extract_filters
from utils.json_completion import json_completion

wait = wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT)

# ── Lazy globals ───────────────────────────────────────────────────────────────
_openai_client = None
_collection = None


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


def _get_collection():
    global _collection
    if _collection is None:
        chroma = PersistentClient(path=CHROMA_DB_DIR)
        _collection = chroma.get_or_create_collection(COLLECTION_NAME)
        count = _collection.count()
        if count == 0:
            raise RuntimeError("Index is empty. Run: python app.py --ingest")
        print(f"[Retrieval] Connected to ChromaDB — {count} chunks indexed.")
    return _collection


# ── Result model (same as chunker.Result for consistency) ─────────────────────

class Result:
    """Simple result container matching the chunker's Result structure."""
    def __init__(self, page_content: str, metadata: dict, score: float = 0.0):
        self.page_content = page_content
        self.metadata = metadata
        self.score = score


# ── Reranker ──────────────────────────────────────────────────────────────────

class RankOrder(BaseModel):
    order: List[int] = Field(
        description="Chunk IDs ranked from most relevant to least relevant"
    )


@retry(wait=wait)
def rerank(question: str, chunks: List[Result]) -> List[Result]:
    """
    Ask the LLM to re-rank retrieved chunks by relevance to the question.
    Uses json_completion for cross-provider compatibility.
    """
    if not chunks:
        return chunks

    system_prompt = """You are a document re-ranker.
You are given a question and a list of text chunks retrieved from a regulatory knowledge base.
Rank the chunks by relevance to the question, most relevant first.
Reply only with the list of ranked chunk IDs. Include all chunk IDs."""

    user_prompt = f"Question:\n\n{question}\n\nRank all chunks by relevance:\n\n"
    for i, chunk in enumerate(chunks):
        user_prompt += f"# CHUNK ID: {i + 1}:\n\n{chunk.page_content[:400]}\n\n"
    user_prompt += "Reply only with the ranked chunk IDs."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    result = json_completion(MODEL, messages, RankOrder)
    order = result.order

    # Safely map back — guard against out-of-range indices
    reranked = []
    seen = set()
    for idx in order:
        i = idx - 1
        if 0 <= i < len(chunks) and i not in seen:
            reranked.append(chunks[i])
            seen.add(i)
    # Append any missing chunks at the end
    for i, c in enumerate(chunks):
        if i not in seen:
            reranked.append(c)
    return reranked


# ── Embedding ─────────────────────────────────────────────────────────────────

def embed_query(question: str) -> List[float]:
    """Embed a single query using OpenAI text-embedding-3-large."""
    client = _get_openai_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=[question])
    return response.data[0].embedding


# ── Single retrieval pass ─────────────────────────────────────────────────────

def fetch_context_unranked(question: str, k: int = RETRIEVAL_K) -> List[Result]:
    """
    Retrieve top-k chunks by cosine similarity, with optional metadata filtering.
    """
    collection = _get_collection()
    filters = extract_filters(question)
    chroma_where = filters.get("chroma_where") or None
    reg_hint = filters.get("reg_hint")

    query_embedding = embed_query(question)

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, collection.count()),
            where=chroma_where if chroma_where else None,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        print(f"[Retrieval] Metadata filter failed ({e}), retrying without filter.")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        score = round(1.0 - dist, 4)
        chunks.append(Result(page_content=doc, metadata=meta, score=score))

    # Soft regulation ID post-filter
    if reg_hint:
        filtered = [
            c for c in chunks
            if reg_hint.lower() in c.metadata.get("source", "").lower()
        ]
        if filtered:
            chunks = filtered

    return chunks


# ── Merge helper ──────────────────────────────────────────────────────────────

def merge_chunks(primary: List[Result], secondary: List[Result]) -> List[Result]:
    """
    Merge two result lists, deduplicating by page_content.
    Primary results come first.
    """
    merged = primary[:]
    existing = {c.page_content for c in primary}
    for chunk in secondary:
        if chunk.page_content not in existing:
            merged.append(chunk)
            existing.add(chunk.page_content)
    return merged


# ── Main retrieval entry point ────────────────────────────────────────────────

def fetch_context(original_question: str, rewritten_question: Optional[str] = None) -> List[Result]:
    """
    Dual retrieval: fetch on both the original and rewritten question,
    merge the results, rerank with the LLM, and return the top FINAL_K chunks.
    """
    chunks1 = fetch_context_unranked(original_question)
    if rewritten_question and rewritten_question != original_question:
        chunks2 = fetch_context_unranked(rewritten_question)
        chunks = merge_chunks(chunks1, chunks2)
    else:
        chunks = chunks1

    reranked = rerank(original_question, chunks)
    return reranked[:FINAL_K]


def get_collection_stats() -> Dict[str, Any]:
    """Return basic stats about the indexed collection."""
    collection = _get_collection()
    total = collection.count()
    all_meta = collection.get(include=["metadatas"])["metadatas"]
    sources = sorted(set(m.get("source", "") for m in all_meta if m.get("source")))
    doc_types = sorted(set(m.get("type", "") for m in all_meta if m.get("type")))
    return {
        "total_chunks": total,
        "doc_types": doc_types,
        "sources": sources,
    }


# Alias for adaptive controller compatibility
def retrieve(question: str, k: int = RETRIEVAL_K, filters: Optional[Dict] = None) -> List[Dict]:
    """
    Thin wrapper used by the adaptive controller.
    Returns dicts for backward compatibility with the adaptive controller.
    """
    chunks = fetch_context_unranked(question, k=k)
    return [
        {
            "chunk_id": str(i),
            "text": c.page_content,
            "metadata": c.metadata,
            "score": c.score,
        }
        for i, c in enumerate(chunks)
    ]