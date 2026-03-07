"""
RAG module: retrieve relevant chunks from Chroma, generate answer via OpenRouter.
Uses same SentenceTransformer as ingest for query embedding. Economical model for class use.
"""
from pathlib import Path
from types import SimpleNamespace

# Load .env from project root
MAKINDA_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MAKINDA_DIR.parent.parent.parent
DOTENV = PROJECT_ROOT / ".env"
if DOTENV.exists():
    from dotenv import load_dotenv
    load_dotenv(DOTENV, override=True)

import os
from chromadb import PersistentClient
from openai import OpenAI
from sentence_transformers import SentenceTransformer

DB_PATH = MAKINDA_DIR / "vector_db"
COLLECTION_NAME = "kuccps_docs"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RETRIEVAL_K = 6
# Economical model via OpenRouter
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
COMPLETION_MODEL = "openai/gpt-4o-mini"

SYSTEM_PROMPT = """You are an expert KUCCPS (Kenya Universities and Colleges Central Placement Service) advisor.
Use ONLY the following context to answer. If the answer is not in the context, say so. Do not invent cut-offs or programme names.
When recommending universities, suggest AT MOST FOUR universities that match the student's cluster and course interest.
Be concise and accurate. Context:

{context}
"""

_embedding_model = None
_chroma_client = None
_openai_client = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def _get_chroma():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = PersistentClient(path=str(DB_PATH))
    return _chroma_client


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "Set OPENROUTER_API_KEY or OPENAI_API_KEY in .env (project root: llm_engineering/.env)"
            )
        base_url = OPENROUTER_BASE if os.getenv("OPENROUTER_API_KEY") else None
        _openai_client = OpenAI(
            api_key=api_key,
            base_url=base_url if base_url else None,
        )
    return _openai_client


def fetch_context(question: str, k: int = RETRIEVAL_K) -> list[SimpleNamespace]:
    """Retrieve up to k most relevant chunks. Returns list of objects with .page_content and .metadata."""
    client = _get_chroma()
    try:
        coll = client.get_collection(name=COLLECTION_NAME)
    except Exception:
        return []
    if coll.count() == 0:
        return []
    model = _get_embedding_model()
    qvec = model.encode([question]).tolist()
    n = min(k, coll.count())
    result = coll.query(
        query_embeddings=qvec,
        n_results=n,
        include=["documents", "metadatas"],
    )
    docs = []
    if result["documents"] and result["documents"][0]:
        for doc_text, meta in zip(
            result["documents"][0],
            result["metadatas"][0] or [{}] * len(result["documents"][0]),
        ):
            docs.append(
                SimpleNamespace(page_content=doc_text, metadata=meta or {})
            )
    return docs


def answer_question(
    question: str,
    cluster_summary: str = "",
) -> str:
    """
    RAG: retrieve context from Chroma, then generate answer via OpenRouter.
    cluster_summary: optional text (e.g. cluster name, weighted points) to include in the prompt.
    """
    docs = fetch_context(question, k=RETRIEVAL_K)
    context = "\n\n---\n\n".join(d.page_content for d in docs) if docs else "(No relevant documents found.)"
    if cluster_summary:
        context = f"Student context: {cluster_summary}\n\n" + context
    system_content = SYSTEM_PROMPT.format(context=context)
    client = _get_openai_client()
    model = COMPLETION_MODEL
    # OpenRouter expects model name as-is (e.g. openai/gpt-4o-mini)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": question},
        ],
        temperature=0.2,
        max_tokens=800,
    )
    return (resp.choices[0].message.content or "").strip()
