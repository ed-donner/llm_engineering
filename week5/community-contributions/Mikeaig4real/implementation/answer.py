"""
Bugs RAG answer pipeline: divide-conquer-merge + rerank.
Combines week5 implementation (LangChain Chroma, history-aware answer) with
pro_implementation (rerank, multi-query). Adds recursive sub-question expansion:
vague questions → LLM-generated sub-questions → retrieve with decaying k → merge → rerank → answer.
"""

import os
import hashlib
import logging
from pathlib import Path
from collections import OrderedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from litellm import completion
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

try:
    from tenacity import retry, wait_exponential
except ImportError:

    def retry(*args, **kwargs):
        def decorator(f):
            return f

        return decorator

    wait_exponential = lambda **kw: (lambda: 0)


load_dotenv(override=True)

# Paths and model (align with ingest: same DB and OpenRouter)
THIS_DIR = Path(__file__).resolve().parent.parent
DB_PATH = THIS_DIR / "vector_db_bugs"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
EMBEDDING_MODEL = "text-embedding-3-large"
MODEL = os.getenv("ANSWER_MODEL", "openrouter/openai/gpt-4o-mini")
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY") or ""

# Retrieval: base k, min k (stopping), decay per level, final context size
RETRIEVAL_K_BASE = 20
K_MIN = 2
K_DECAY = 5
FINAL_K = 10
MAX_MERGED_BEFORE_RERANK = 40  # cap before rerank to avoid token blow-up
CACHE_MAX_SIZE = 128  # max (query_hash, k) entries

SYSTEM_PROMPT = """You are a knowledgeable assistant for a bugs knowledge base (code bugs, types, locations, timestamps).
Use the given context to answer the question accurately. If the context does not contain enough information, say so.
Be concise and cite bug IDs or sections when relevant.

Context:
{context}
"""

MD_STRUCTURE = """
Each .md file has this exact structure:
- Line 1: # Bug #<id>
- Then key-value block: **Level:**, **Description:**, **Bug Types:**, **Bug Count:**, **Tags:**, **Created:**, **Model:**
- ## Correct Code → fenced ```python ... ``` block
- ## Buggy Code → fenced ```python ... ``` block
- ## Bugs Injected → markdown table with columns # | Line | Type | Description
"""


# --- Caching: avoid re-retrieving same (question, k) across recursive calls ---
_retrieve_cache: OrderedDict = OrderedDict()


def _cache_key(question: str, k: int) -> tuple[str, int]:
    h = hashlib.sha256(question.strip().encode()).hexdigest()[:16]
    return (h, k)


def _cache_get(key: tuple) -> list[Document] | None:
    if key in _retrieve_cache:
        logging.info(f"[LOG] Cache hit for key: {key}")
        _retrieve_cache.move_to_end(key)
        return _retrieve_cache[key]
    logging.info(f"[LOG] Cache miss for key: {key}")
    return None


def _cache_set(key: tuple, value: list[Document]) -> None:
    if key in _retrieve_cache:
        _retrieve_cache.move_to_end(key)
    _retrieve_cache[key] = value
    while len(_retrieve_cache) > CACHE_MAX_SIZE:
        logging.info(f"[LOG] Cache size exceeded, popping oldest item")
        _retrieve_cache.popitem(last=False)


# --- Lazy vectorstore (same as ingest: OpenRouter embeddings + Chroma) ---
_vectorstore: Chroma | None = None


def _get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        logging.info("[LOG] Initializing vectorstore with OpenAIEmbeddings and Chroma")
        embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_base=OPENROUTER_BASE,
        )
        _vectorstore = Chroma(
            persist_directory=str(DB_PATH),
            embedding_function=embeddings,
        )
    return _vectorstore


# --- Specificity / sub-questions (divide step) ---
class SpecificityResult(BaseModel):
    """Either the question is specific (retrieve directly) or we need sub-questions."""

    specific: bool = Field(
        description="True if the question is already specific enough to retrieve directly; False if it is vague and should be split into sub-questions."
    )
    sub_questions: list[str] = Field(
        default_factory=list,
        description="If specific is False, 1-3 concrete sub-questions that together cover the original. Empty if specific is True.",
    )


@retry(wait=wait_exponential(multiplier=1, min=2, max=60))
def _is_specific_or_subquestions(question: str) -> tuple[bool, list[str]]:
    logging.info(f"[LOG] _is_specific_or_subquestions called with question: {question}")
    """Returns (is_specific, sub_questions). If specific, sub_questions is empty."""
    prompt = f"""
You are an expert on a Python code bug knowledge base. The knowledge base consists of bug reports, each with:
- Level (difficulty)
- Description (what the code does)
- Correct code (bug-free Python function)
- Buggy code (with injected bugs)
- Bug types (e.g., LogicError, NameError, TypeError, etc.)
- Number of bugs and details (line, type, description)
- Tags (e.g., string, math, error-handling, etc.)
- Model used to generate
- Creation date

The markdown file structure for each bug is:
{MD_STRUCTURE}

You must only answer or break down questions that are strictly about these bug reports, their code, bug types, and metadata. Never ask about anything outside this domain.

Analyze the following question:
"""
    prompt += f'\nQuestion: "{question[:800]}"\n'
    prompt += """
Decide:
- SPECIFIC: The question is concrete (e.g. "In which function does NameError occur on line 5?" or "When was the bug in convert_to_uppercase created?"). One retrieval can answer it.
- VAGUE: The question is broad or multi-part (e.g. "Tell me about all LogicErrors" or "What bugs were added in January and where?"). It should be split into 1-5 smaller, specific sub-questions that each can be answered with one retrieval.

If VAGUE, provide sub_questions that are:
- Concrete, non-overlapping, and strictly about the bug reports, their code, bug types, or metadata.
- Each sub-question must be fundamentally different from the others (not just rephrasings or minor variations).
- Do NOT generate sub-questions that are rephrasings, only change focus, scope, or aspect.
- Avoid splitting by trivial differences (e.g., just changing a word or order).
- Do not invent unrelated sub-questions or go outside the knowledge base.
If SPECIFIC, set specific=true and leave sub_questions empty.
"""
    kwargs = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": SpecificityResult,
    }
    if API_KEY:
        kwargs["api_key"] = API_KEY
    resp = completion(**kwargs)
    out = SpecificityResult.model_validate_json(resp.choices[0].message.content)
    logging.info(
        f"[LOG] SpecificityResult: specific={out.specific}, sub_questions={out.sub_questions}"
    )
    if out.specific:
        return True, []
    sub = [s.strip() for s in out.sub_questions if s.strip()][:5]
    return False, sub


# --- Retrieve (single query, no rewrite) ---
def _retrieve(question: str, k: int) -> list[Document]:
    logging.info(f"[LOG] _retrieve called with question: {question}, k: {k}")
    key = _cache_key(question, k)
    cached = _cache_get(key)
    if cached is not None:
        logging.info(
            f"[LOG] Returning cached result for key: {key}, docs: {len(cached)}"
        )
        return cached
    vs = _get_vectorstore()
    docs = vs.similarity_search(question, k=k)
    logging.info(
        f"[LOG] Retrieved {len(docs)} docs from vectorstore for question: {question}"
    )
    _cache_set(key, docs)
    return docs


def _dedupe_docs(docs: list[Document]) -> list[Document]:
    logging.info(f"[LOG] _dedupe_docs called with {len(docs)} docs")
    seen: set[str] = set()
    out: list[Document] = []
    for d in docs:
        h = hashlib.sha256(d.page_content.encode()).hexdigest()
        if h not in seen:
            seen.add(h)
            out.append(d)
    logging.info(f"[LOG] Deduped docs count: {len(out)}")
    return out


def _flat_gather(question: str, k: int) -> list[Document]:
    """
    Non-recursive: If question is specific, retrieve. If vague, generate 1-5 sub-questions, retrieve for each, merge, dedupe.
    """
    logging.info(f"[LOG] _flat_gather called with question: {question}, k: {k}")
    is_specific, sub_questions = _is_specific_or_subquestions(question)
    logging.info(f"[LOG] is_specific: {is_specific}, sub_questions: {sub_questions}")
    if is_specific or not sub_questions:
        logging.info(f"[LOG] Specific or no sub-questions, retrieving with k={k}")
        return _retrieve(question, k)
        
    merged: list[Document] = []
    for sq in sub_questions:
        logging.info(f"[LOG] Gathering for sub-question: {sq}")
        docs = _retrieve(sq, max(K_MIN, k - K_DECAY))
        merged.extend(docs)
        
    deduped = _dedupe_docs(merged)
    logging.info(f"[LOG] Merged and deduped {len(deduped)} docs from sub-questions")
    return deduped


# --- Rerank (pro_implementation style: LLM orders by relevance) ---
class RankOrder(BaseModel):
    order: list[int] = Field(
        description="List of chunk ids (1-based) in order of relevance to the question, most relevant first. Include every id exactly once."
    )


@retry(wait=wait_exponential(multiplier=1, min=2, max=60))
def _rerank(question: str, chunks: list[Document]) -> list[Document]:
    logging.info(
        f"[LOG] _rerank called with question: {question}, chunks: {len(chunks)}"
    )
    """Re-order chunks by relevance to question using LLM."""
    if not chunks:
        logging.warning("[LOG] No chunks to rerank")
        return []
    if len(chunks) == 1:
        logging.info("[LOG] Only one chunk, no rerank needed")
        return chunks
    system = """You are a re-ranker. Given a question and numbered chunks, output the chunk ids in order of relevance (most relevant first). Include every id exactly once."""
    user = f"Question:\n{question}\n\nChunks:\n"
    for i, c in enumerate(chunks):
        user += f"# CHUNK ID: {i + 1}:\n{c.page_content[:2000]}\n\n"
    user += "Reply with the list of chunk ids in relevance order (e.g. [2, 1, 3])."
    kwargs = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": RankOrder,
    }
    if API_KEY:
        kwargs["api_key"] = API_KEY
    resp = completion(**kwargs)
    order = RankOrder.model_validate_json(resp.choices[0].message.content).order
    logging.info(f"[LOG] Rerank order: {order}")
    # Normalize: 1-based ids; include each chunk at most once
    used = set()
    result = []
    for idx in order:
        if isinstance(idx, int) and 1 <= idx <= len(chunks) and idx not in used:
            used.add(idx)
            result.append(chunks[idx - 1])
    for i in range(1, len(chunks) + 1):
        if i not in used:
            result.append(chunks[i - 1])
    return result


# --- Messages for final answer (week5 + pro: context with source, history) ---
def _make_rag_messages(
    question: str, history: list[dict], chunks: list[Document]
) -> list[dict]:
    logging.info(
        f"[LOG] _make_rag_messages called with question: {question}, history: {history}, chunks: {len(chunks)}"
    )
    context = "\n\n".join(
        f"From {chunk.metadata.get('source', 'unknown')}:\n{chunk.page_content}"
        for chunk in chunks
    )
    system = SYSTEM_PROMPT.format(context=context)
    messages = [{"role": "system", "content": system}]
    for m in history:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": question})
    logging.info(f"[LOG] _make_rag_messages result: {messages}")
    return messages


def combined_question(question: str, history: list[dict] | None = None) -> str:
    logging.info(
        f"[LOG] combined_question called with question: {question}, history: {history}"
    )
    history = history or []
    prior = "\n".join(
        m["content"] for m in history if m.get("role") == "user" and m.get("content")
    )
    if not prior.strip():
        return question.strip()
    combined = (prior + "\n" + question).strip()
    logging.info(f"[LOG] combined_question result: {combined}")
    return combined


# --- Public API ---
def fetch_context(question: str) -> list[Document]:
    logging.info(f"[LOG] fetch_context called with question: {question}")
    gathered = _flat_gather(question, RETRIEVAL_K_BASE)
    logging.info(
        f"[LOG] Gathered {len(gathered) if gathered else 0} docs after flat gather"
    )
    if not gathered:
        logging.warning("[LOG] No documents gathered in fetch_context")
        return []
    merged = _dedupe_docs(gathered)[:MAX_MERGED_BEFORE_RERANK]
    logging.info(f"[LOG] Merged and deduped docs: {len(merged)}")
    reranked = _rerank(question, merged)
    logging.info(f"[LOG] Reranked docs: {len(reranked)}")
    return reranked[:FINAL_K]


@retry(wait=wait_exponential(multiplier=1, min=2, max=60))
def answer_question(
    question: str, history: list[dict] | None = None
) -> tuple[str, list[Document]]:
    """
    Answer the question with RAG: fetch_context (divide-conquer-merge + rerank) then LLM.
    Returns (answer_text, retrieved_docs).
    """
    history = history or []
    combined = combined_question(question, history)
    docs = fetch_context(combined)
    if not docs:
        return (
            "I couldn't find any relevant bug entries for that question. Try rephrasing or asking about a specific bug, function, or error type.",
            docs,
        )
    messages = _make_rag_messages(question, history, docs)
    kwargs = {"model": MODEL, "messages": messages}
    if API_KEY:
        kwargs["api_key"] = API_KEY
    response = completion(**kwargs)
    answer = response.choices[0].message.content or ""
    return answer, docs
