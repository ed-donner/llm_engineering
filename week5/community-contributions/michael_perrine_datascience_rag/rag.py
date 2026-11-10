"""Data Science RAG: retrieval + answer pipeline shared by the notebook and the Streamlit app.

The logic mirrors the notebook's "RAG Chain" cell, which was evaluated in Steps 9-9d:
  1. search()  - embed the question, call the match_documents RPC (page-level chunks)
  2. gate      - refuse without an LLM call if the best similarity is below MIN_SIM
  3. LLM       - structured Answer; in_context is decided FIRST (second refusal layer)
  4. cite()    - citations are built in code from Supabase metadata, never by the LLM

Entry points:
  ask(question)        -> result dict (non-streaming; used by the notebook and the eval)
  ask_stream(question) -> yields ("token", text) while the answer streams, then one final
                          ("done", result) or ("refused", result)

Secrets come from environment variables: .env locally, Streamlit secrets on deploy
(top-level keys in secrets.toml are exposed as environment variables).
Importing this module makes no network calls; clients are created on first use.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Iterator

from dotenv import load_dotenv
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field
from supabase import Client, create_client

load_dotenv()  # no override: variables set by the host (e.g. Streamlit Cloud) win over .env

# --- Config ---
MODEL = "gpt-6-luna"                    # bare model name for ChatOpenAI
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 1536             # must match vector(1536) in Supabase
TABLE_NAME = "documents"
MATCH_FUNCTION = "match_documents"
DEFAULT_STRATEGY = "page"               # chosen in Step 9d (page vs section)

MIN_SIM = 0.40                          # layer-1 gate, tuned with the Step 9 cutoff sweep
TOP_K = 5
REFUSAL = "I couldn't find this in the documentation with enough confidence."
LIBRARIES = ("matplotlib", "numpy", "pandas", "plotly", "scikit-learn", "scipy")

# USD per 1M tokens: verify at developers.openai.com/api/docs/pricing
PRICES = {MODEL: {"input": 0.10, "cached": 0.01, "output": 0.50}}
NO_USAGE = {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}

REQUIRED_ENV = ("OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_KEY")


class Answer(BaseModel):
    # in_context comes FIRST so the model judges coverage before it starts writing an answer.
    in_context: bool = Field(description="""True only if the context blocks directly answer the question.
        False if the question is about a library, tool or feature the blocks don't cover, even when the blocks
        discuss something similar or only mention it by name. If your answer would have to say the context doesn't
        show how, set False.""")
    answer: str = Field(description="""Answer using only the context. Include a short code example when helpful.
    If in_context is False, say in one sentence what the context covers instead.""")
    cited: list[int] = Field(description="""Numbers of the context blocks the answer relies on, e.g. [1, 3].
    Empty if in_context is False.""")


prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a documentation assistant for data science libraries. Answer ONLY from the numbered
    context blocks. Each block is labeled with the library it comes from. If the question asks about a library
    or tool that none of the blocks come from, set in_context to False. Do not answer it with a different
    library's equivalent. Never make up an answer. List the block numbers you used only in `cited`; do not
    include block numbers in the answer text."""),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])


# --- Clients (lazy, one per process) ---
def _check_env() -> None:
    missing = [v for v in REQUIRED_ENV if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    _check_env()
    return OpenAIEmbeddings(model=EMBEDDING_MODEL, dimensions=EMBEDDING_DIMENSIONS)


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    _check_env()
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


@lru_cache(maxsize=1)
def get_llm():
    """Non-streaming: same construction as the evaluated notebook cell."""
    _check_env()
    return ChatOpenAI(model=MODEL).with_structured_output(Answer, include_raw=True)


@lru_cache(maxsize=1)
def get_stream_llm():
    """Streaming: a JSON-schema dict (not the Pydantic class) makes LangChain yield partial dicts."""
    _check_env()
    return ChatOpenAI(model=MODEL, stream_usage=True).with_structured_output(
        Answer.model_json_schema(), method="json_schema")


# --- Helpers ---
def llm_cost(usage: dict, model: str = MODEL) -> float:
    p = PRICES[model]
    cached = (usage.get("input_token_details") or {}).get("cache_read", 0) or 0
    return ((usage["input_tokens"] - cached) * p["input"] + cached * p["cached"]
            + usage["output_tokens"] * p["output"]) / 1e6


def _usage(usage: dict | None) -> dict:
    if not usage:
        return dict(NO_USAGE)
    return {"input_tokens": usage["input_tokens"], "output_tokens": usage["output_tokens"],
            "cost": llm_cost(usage)}


def cite(hit: dict) -> dict:
    m = hit["metadata"]
    end = m.get("page_end", m["page"])
    pages = str(m["page"]) if m["page"] == end else f'{m["page"]}-{end}'
    return {"library": m["library"], "version": m["version"], "section": m["section"],
            "pages": pages, "url": m.get("source_url"), "sim": round(hit["similarity"], 3)}


def dedupe(sources: list[dict]) -> list[dict]:
    """Keep the FIRST (best-scoring) source per (library, section)."""
    out = {}
    for s in sources:
        out.setdefault((s["library"], s["section"]), s)
    return list(out.values())


def build_context(hits: list[dict]) -> str:
    return "\n\n".join(f"[{i}] {h['metadata']['library']} · {h['metadata']['section']}\n{h['content']}"
                       for i, h in enumerate(hits, 1))


# --- Pipeline ---
def search(question: str, k: int = TOP_K, qv: list[float] | None = None,
           strategy: str = DEFAULT_STRATEGY, **filters) -> list[dict]:
    """Top-k chunks via the match_documents RPC. Pass qv to reuse a cached question vector."""
    qv = qv if qv is not None else get_embeddings().embed_query(question)
    return get_supabase().rpc(MATCH_FUNCTION, {"query_embedding": qv,
                                               "match_count": k,
                                               "filter": {"strategy": strategy, **filters},
                                               }).execute().data


def _gate(hits: list[dict]) -> tuple[list[dict], dict | None]:
    """Layer 1. Returns (nearest sources, gate-refusal result or None)."""
    near = dedupe([cite(h) for h in hits[:3]])
    if not hits or hits[0]["similarity"] < MIN_SIM:
        return near, {"answer": REFUSAL, "sources": near, "confident": False,
                      "refused_by": "gate", "context": None, **NO_USAGE}
    return near, None


def _finish(out: Answer, hits: list[dict], near: list[dict], context: str, usage: dict) -> dict:
    """Layer 2 (LLM in_context) plus citations from the blocks the LLM cited."""
    if not out.in_context:
        return {"answer": REFUSAL, "sources": near, "confident": False, "refused_by": "llm",
                "llm_note": out.answer, "context": context, **usage}
    used = [hits[i - 1] for i in out.cited if 1 <= i <= len(hits)]
    return {"answer": out.answer, "sources": dedupe([cite(h) for h in used]), "confident": True,
            "refused_by": None, "context": context, **usage}


def ask(question: str, k: int = TOP_K, qv: list[float] | None = None,
        strategy: str = DEFAULT_STRATEGY, **filters) -> dict:
    hits = search(question, k, qv=qv, strategy=strategy, **filters)
    near, refused = _gate(hits)
    if refused:
        return refused
    context = build_context(hits)
    res = (prompt | get_llm()).invoke({"context": context, "question": question})
    if res["parsed"] is None:
        raise ValueError(res["parsing_error"])
    return _finish(res["parsed"], hits, near, context, _usage(res["raw"].usage_metadata))


def ask_stream(question: str, k: int = TOP_K, qv: list[float] | None = None,
               strategy: str = DEFAULT_STRATEGY, **filters) -> Iterator[tuple[str, object]]:
    """Yield ("token", text) as the answer streams, then ("done", result) or ("refused", result).

    Answer text is only streamed once in_context is True, so refusals never flash partial text.
    """
    hits = search(question, k, qv=qv, strategy=strategy, **filters)
    near, refused = _gate(hits)
    if refused:
        yield "refused", refused
        return

    context = build_context(hits)
    cb = UsageMetadataCallbackHandler()
    sent, last = "", {}
    for part in (prompt | get_stream_llm()).stream({"context": context, "question": question},
                                                   config={"callbacks": [cb]}):
        last = part
        if part.get("in_context") is True:
            text = part.get("answer") or ""
            if len(text) > len(sent) and text.startswith(sent):  # partial JSON grows as a prefix
                yield "token", text[len(sent):]
                sent = text

    usage = next(iter(cb.usage_metadata.values()), None)   # keyed by the model name the API returns
    result = _finish(Answer(**last), hits, near, context, _usage(usage))
    yield ("done" if result["confident"] else "refused"), result
