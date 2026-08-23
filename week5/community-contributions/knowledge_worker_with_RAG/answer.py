"""
RAG answer module: retrieve relevant chunks from Chroma and generate an answer via LiteLLM.
Uses OpenAI text-embedding-3-small for queries and openai/gpt-4o-mini for completion.
"""
from pathlib import Path
import re
from types import SimpleNamespace

from dotenv import load_dotenv

load_dotenv(override=True)

from chromadb import PersistentClient
from litellm import completion
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parent
DB_NAME = str(PROJECT_ROOT / "vector_db")
COLLECTION_NAME = "docs"
EMBEDDING_MODEL = "text-embedding-3-small"
COMPLETION_MODEL = "openai/gpt-4o-mini"
RETRIEVAL_K = 10
SHORT_QUERY_K = 3
MEDIUM_QUERY_K = 6
DISTANCE_MARGIN = 0.35

SMALLTALK_PHRASES = {
    "hi",
    "hello",
    "hey",
    "hey there",
    "yo",
    "sup",
    "good morning",
    "good afternoon",
    "good evening",
}

SYSTEM_PROMPT = """You are a helpful assistant that answers questions about LiteLLM (the library for calling 100+ LLMs with a single API). Use ONLY the following context from the LiteLLM documentation. If the answer is not in the context, say so. Do not make up details.

Context:
{context}
"""

_client: OpenAI | None = None


def _get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def _get_collection():  # Chroma 1.x: returns Collection
    chroma = PersistentClient(path=DB_NAME)
    return chroma.get_or_create_collection(name=COLLECTION_NAME)


def _content_to_text(content: object) -> str:
    """Normalize Gradio/OpenAI-style content blocks to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, dict):
                # Gradio/OpenAI text block: {"type": "text", "text": "..."}
                text_value = item.get("text")
                if isinstance(text_value, str):
                    chunks.append(text_value)
                    continue
                nested_content = item.get("content")
                if isinstance(nested_content, str):
                    chunks.append(nested_content)
                    continue
            chunks.append(str(item))
        return "\n".join(c for c in chunks if c)
    if isinstance(content, dict):
        text_value = content.get("text")
        if isinstance(text_value, str):
            return text_value
        nested_content = content.get("content")
        if isinstance(nested_content, str):
            return nested_content
    return str(content)


def _normalize_text(text: str) -> str:
    lowered = text.strip().lower()
    lowered = re.sub(r"\s+", " ", lowered)
    return re.sub(r"[^\w\s]", "", lowered)


def _is_smalltalk_only(text: str) -> bool:
    normalized = _normalize_text(text)
    if not normalized:
        return True
    if normalized in SMALLTALK_PHRASES:
        return True
    words = normalized.split()
    basic_greetings = {"hi", "hello", "hey", "yo", "sup", "привет", "здравствуйте"}
    return len(words) <= 2 and all(word in basic_greetings for word in words)


def _choose_retrieval_k(text: str) -> int:
    word_count = len(re.findall(r"\w+", text))
    if word_count <= 3:
        return SHORT_QUERY_K
    if word_count <= 8:
        return MEDIUM_QUERY_K
    return RETRIEVAL_K


def fetch_context(question: str, k: int = RETRIEVAL_K) -> list[SimpleNamespace]:
    """
    Retrieve up to k most relevant chunks for the question.
    Returns list of objects with .page_content and .metadata (source, type).
    """
    coll = _get_collection()
    if coll.count() == 0:
        return []
    client = _get_openai_client()
    emb = client.embeddings.create(model=EMBEDDING_MODEL, input=[question])
    qvec = emb.data[0].embedding
    n_results = min(max(k * 2, 6), coll.count())
    result = coll.query(
        query_embeddings=[qvec],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    docs = []
    if result["documents"] and result["documents"][0]:
        doc_row = result["documents"][0]
        meta_row = result["metadatas"][0] or []
        distance_row = (result.get("distances") or [[]])[0]
        best_distance = min(distance_row) if distance_row else None
        for idx, doc_text in enumerate(doc_row):
            meta = meta_row[idx] if idx < len(meta_row) else {}
            distance = distance_row[idx] if idx < len(distance_row) else None
            if best_distance is not None and distance is not None:
                if distance > best_distance + DISTANCE_MARGIN:
                    continue
            docs.append(
                SimpleNamespace(
                    page_content=doc_text,
                    metadata={**(meta or {}), "distance": distance},
                )
            )
            if len(docs) >= k:
                break
    return docs


def combined_question(question: str, history: list[dict]) -> str:
    """Build a single query string from conversation history (user messages) and current question."""
    parts = [
        _content_to_text(m.get("content", ""))
        for m in history
        if m.get("role") == "user" and m.get("content") is not None
    ]
    parts.append(_content_to_text(question))
    return "\n".join(p for p in parts if p)


def answer_question(question: str, history: list[dict] | None = None) -> tuple[str, list[SimpleNamespace]]:
    """
    Answer the question using RAG: retrieve context from Chroma, then call the LLM.
    Returns (answer_text, list of retrieved doc objects with .page_content and .metadata).
    """
    history = history or []
    question_text = _content_to_text(question)
    combined = combined_question(question_text, history)
    docs = []
    if not _is_smalltalk_only(question_text):
        docs = fetch_context(combined, k=_choose_retrieval_k(question_text))
    context = "\n\n---\n\n".join(doc.page_content for doc in docs) if docs else "(No relevant documentation found.)"
    system_content = SYSTEM_PROMPT.format(context=context)
    messages = [{"role": "system", "content": system_content}]
    for m in history:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            messages.append({"role": m["role"], "content": _content_to_text(m["content"])})
    messages.append({"role": "user", "content": question_text})
    response = completion(model=COMPLETION_MODEL, messages=messages)
    answer = response.choices[0].message.content or ""
    return answer, docs
