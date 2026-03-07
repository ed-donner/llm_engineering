"""
get_sentiment        — DistilRoberta local classifier
get_rag_context      — ChromaDB semantic search
cross_check          — GPT-4o contrarian analysis
safeguard_check      — GPT-4o JSON safety audit
write_brief          — GPT-4o final investment brief
store_article        — Persist to ChromaDB for future RAG
fetch_news           — Finnhub live news fetch
send_notification    — Pushover phone alert
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any

import openai
import requests
from transformers import pipeline as hf_pipeline

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from config import APP_CONFIG

_seen_article_ids: set[str] = set()

logger = logging.getLogger(__name__)


#Embedding function

class HuggingFaceEmbeddingFunction:
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model = SentenceTransformer(model_name)

    def name(self) -> str:
        return f"huggingface-{self._model_name}"

    def __call__(self, input: list[str]) -> list[list[float]]:   
        return self._model.encode(input, show_progress_bar=False).tolist()

    def embed_documents(self, input: list[str]) -> list[list[float]]:  
        return self.__call__(input)

    def embed_query(self, input: list[str]) -> list[list[float]]: 
        return self.__call__(input)


#Lazy singletons (loaded once, reused across all tool calls)

_sentiment_pipe = None
_chroma_collection = None
_embedding_fn = None


def _get_sentiment_pipe():
    global _sentiment_pipe
    if _sentiment_pipe is None:
        logger.info("Loading DistilRoberta sentiment model...")
        _sentiment_pipe = hf_pipeline(
            "text-classification",
            model=APP_CONFIG.models.sentiment_model,
            truncation=True,
            max_length=512,
        )
    return _sentiment_pipe


def _get_collection():
    global _chroma_collection, _embedding_fn
    if _chroma_collection is None:
        _embedding_fn = HuggingFaceEmbeddingFunction(APP_CONFIG.models.embedding_model)
        client = chromadb.PersistentClient(
            path=APP_CONFIG.vector_store.persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        _chroma_collection = client.get_or_create_collection(
            name=APP_CONFIG.vector_store.collection_name,
            embedding_function=_embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
    return _chroma_collection


def _openai_client() -> openai.OpenAI:
    return openai.OpenAI(api_key=APP_CONFIG.openai_api_key)


def _openrouter_client() -> openai.OpenAI:
    return openai.OpenAI(
        api_key=APP_CONFIG.openrouter_api_key,
        base_url=APP_CONFIG.models.openrouter_base_url,
        default_headers={"X-Title": "AI Financial News Analyst"},
    )



#Tool functions

def get_sentiment(text: str) -> dict[str, Any]:
    """
    Classify the financial sentiment of a news article.
    Returns label (positive/negative/neutral) and confidence score.
    """
    pipe   = _get_sentiment_pipe()
    result = pipe(text)[0]
    label  = result["label"].lower()
    score  = round(result["score"], 4)
    logger.info("[Tool:get_sentiment] %s %.4f", label, score)
    return {"label": label, "score": score}


def get_rag_context(text: str) -> dict[str, Any]:
    """
    Retrieve the top-N most semantically similar past articles
    from ChromaDB to use as analyst context.
    """
    collection = _get_collection()
    count      = collection.count()
    if count == 0:
        return {"articles": [], "count": 0}

    n       = min(APP_CONFIG.vector_store.n_results, count)
    results = collection.query(
        query_texts=[text],
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )
    articles = [
        {
            "text":      results["documents"][0][i][:300],
            "metadata":  results["metadatas"][0][i],
            "distance":  round(results["distances"][0][i], 4),
        }
        for i in range(len(results["ids"][0]))
    ]
    logger.info("[Tool:get_rag_context] retrieved %d docs", len(articles))
    return {"articles": articles, "count": len(articles)}


def cross_check(article: str, analysis: str) -> dict[str, str]:
    """
    GPT-4o provides a contrarian / devil's advocate view on the
    primary analysis to reduce single-model bias.
    """
    client = _openai_client()
    resp   = client.chat.completions.create(
        model=APP_CONFIG.models.gpt_model,
        max_tokens=APP_CONFIG.models.gpt_max_tokens,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a contrarian financial analyst. Challenge the consensus view. "
                    "If the analysis is bullish, find overlooked risks. "
                    "If bearish, find missed opportunities. Max 200 words. Be direct."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Article:\n{article}\n\n"
                    f"Primary analysis:\n{analysis}\n\n"
                    "What is the contrarian perspective?"
                ),
            },
        ],
    )
    result = resp.choices[0].message.content.strip()
    logger.info("[Tool:cross_check] done (%d chars)", len(result))
    return {"contrarian_view": result}


def safeguard_check(article: str, analysis: str, contrarian: str) -> dict[str, Any]:
    """
    GPT-4o audits all outputs for hallucinations, alarmist language,
    and market-manipulation phrasing. Returns PASS / WARN / FAIL + flags.
    """
    client = _openai_client()
    resp   = client.chat.completions.create(
        model=APP_CONFIG.models.gpt_model,
        max_tokens=512,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI safety auditor for financial content. "
                    "Check for: (1) hallucinations not supported by the article, "
                    "(2) alarmist or misleading language, "
                    "(3) market-manipulation phrasing. "
                    'Return ONLY JSON: {"verdict":"PASS"|"WARN"|"FAIL","flags":["..."]}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Article:\n{article}\n\n"
                    f"Analysis:\n{analysis}\n\n"
                    f"Contrarian view:\n{contrarian}"
                ),
            },
        ],
    )
    raw = resp.choices[0].message.content.strip()
    try:
        parsed  = json.loads(raw)
        verdict = parsed.get("verdict", "WARN")
        flags   = parsed.get("flags", [])
    except json.JSONDecodeError:
        verdict, flags = "WARN", ["Could not parse safeguard response."]
    logger.info("[Tool:safeguard_check] verdict=%s flags=%d", verdict, len(flags))
    return {"verdict": verdict, "flags": flags}


def write_brief(
    article: str,
    sentiment_label: str,
    sentiment_score: float,
    analysis: str,
    contrarian: str,
    safeguard_verdict: str,
    safeguard_flags: list[str],
) -> dict[str, str]:
    """
    GPT-4o synthesises all agent outputs into a final structured
    investment brief with recommendation.
    """
    client     = _openai_client()
    flags_text = ", ".join(safeguard_flags) if safeguard_flags else "None"
    resp       = client.chat.completions.create(
        model=APP_CONFIG.models.gpt_model,
        max_tokens=APP_CONFIG.models.gpt_max_tokens,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are head of research at an asset management firm. "
                    "Write a concise investment brief using this structure:\n"
                    "**Executive Summary** (2 sentences)\n"
                    "**Sentiment Verdict**\n"
                    "**Bull Case**\n"
                    "**Bear Case**\n"
                    "**Risk Flags**\n"
                    "**Recommendation** (Buy / Hold / Avoid / Monitor)\n"
                    "If safeguard verdict is FAIL, open with a prominent warning."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Article: {article}\n\n"
                    f"Sentiment: {sentiment_label} ({sentiment_score:.2%})\n\n"
                    f"Analysis:\n{analysis}\n\n"
                    f"Contrarian view:\n{contrarian}\n\n"
                    f"Safeguard verdict: {safeguard_verdict}\n"
                    f"Safeguard flags: {flags_text}\n\n"
                    "Write the investment brief."
                ),
            },
        ],
    )
    brief = resp.choices[0].message.content.strip()
    logger.info("[Tool:write_brief] done (%d chars)", len(brief))
    return {"brief": brief}


def store_article(
    text: str,
    sentiment_label: str,
    sentiment_score: float,
    safeguard_verdict: str,
) -> dict[str, str]:
    """
    Persist a news article and its metadata to ChromaDB so it can
    be retrieved as RAG context in future analyses.
    """
    import hashlib
    collection = _get_collection()
    doc_id     = hashlib.sha256(text.encode()).hexdigest()[:32]
    collection.upsert(
        ids=[doc_id],
        documents=[text],
        metadatas=[{
            "ingested_at":  datetime.utcnow().isoformat(),
            "sentiment":    sentiment_label,
            "score":        str(sentiment_score),
            "safeguard":    safeguard_verdict,
        }],
    )
    logger.info("[Tool:store_article] upserted %s", doc_id)
    return {"stored_id": doc_id}


def fetch_news(category: str = "crypto", limit: int = 20) -> dict[str, Any]:
    global _seen_article_ids

    url  = f"{APP_CONFIG.news.finnhub_base_url}/news"
    resp = requests.get(
        url,
        params={"category": category},
        headers={"X-Finnhub-Token": APP_CONFIG.finnhub_api_key},
        timeout=10,
    )
    resp.raise_for_status()
    raw      = resp.json()
    articles = []

    for a in raw:
        if not (a.get("headline") and a.get("summary")):
            continue

        # Use Finnhub's article id as the dedup key
        article_id = str(a.get("id", ""))

        if article_id and article_id in _seen_article_ids:
            continue   # already analysed this one — skip

        articles.append({
            "headline":     a.get("headline", "").strip(),
            "summary":      a.get("summary", "").strip(),
            "source":       a.get("source", "unknown"),
            "related":      a.get("related", ""),
            "published_at": datetime.utcfromtimestamp(
                                a.get("datetime", 0)
                            ).isoformat(),
            "url":          a.get("url", ""),
            "_id":          article_id,
        })

        if len(articles) >= limit:
            break

    # Mark all fetched articles as seen
    for a in articles:
        if a["_id"]:
            _seen_article_ids.add(a["_id"])

    logger.info(
        "[Tool:fetch_news] %d new articles (skipped %d already seen, total seen: %d)",
        len(articles),
        len(raw) - len(articles),
        len(_seen_article_ids),
    )
    return {"articles": articles, "count": len(articles)}


def send_notification(
    title: str,
    message: str,
    priority: int = 0,
) -> dict[str, Any]:
    """
    Send a push notification to the user's phone via Pushover.
    Priority: -1 (quiet), 0 (normal), 1 (high), 2 (require confirmation).
    """
    payload = {
        "token":    APP_CONFIG.pushover_app_token,
        "user":     APP_CONFIG.pushover_user_key,
        "title":    title[:250],
        "message":  message[:1024],
        "priority": priority,
    }
    try:
        resp = requests.post(APP_CONFIG.pushover.api_url, data=payload, timeout=10)
        resp.raise_for_status()
        logger.info("[Tool:send_notification] sent: %s", title)
        return {"sent": True, "title": title}
    except requests.RequestException as exc:
        logger.error("[Tool:send_notification] failed: %s", exc)
        return {"sent": False, "error": str(exc)}



TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_sentiment",
            "description": "Classify the financial sentiment of a news article using DistilRoberta. Returns label (positive/negative/neutral) and confidence score.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The news article text to classify."}
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rag_context",
            "description": "Retrieve semantically similar past articles from ChromaDB to use as context for analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The current article text to find similar articles for."}
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cross_check",
            "description": "Get a contrarian / devil's advocate view from GPT-4o to challenge the primary analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "article":  {"type": "string", "description": "The original news article."},
                    "analysis": {"type": "string", "description": "The primary analysis to challenge."},
                },
                "required": ["article", "analysis"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "safeguard_check",
            "description": "Audit all outputs for hallucinations, alarmist language, and market-manipulation phrasing. Returns PASS/WARN/FAIL verdict.",
            "parameters": {
                "type": "object",
                "properties": {
                    "article":    {"type": "string"},
                    "analysis":   {"type": "string"},
                    "contrarian": {"type": "string"},
                },
                "required": ["article", "analysis", "contrarian"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_brief",
            "description": "Synthesise all analysis outputs into a structured investment brief with a Buy/Hold/Avoid/Monitor recommendation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "article":           {"type": "string"},
                    "sentiment_label":   {"type": "string"},
                    "sentiment_score":   {"type": "number"},
                    "analysis":          {"type": "string"},
                    "contrarian":        {"type": "string"},
                    "safeguard_verdict": {"type": "string"},
                    "safeguard_flags":   {"type": "array", "items": {"type": "string"}},
                },
                "required": ["article", "sentiment_label", "sentiment_score",
                             "analysis", "contrarian", "safeguard_verdict", "safeguard_flags"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "store_article",
            "description": "Persist the analysed article and metadata to ChromaDB for future RAG context retrieval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text":              {"type": "string"},
                    "sentiment_label":   {"type": "string"},
                    "sentiment_score":   {"type": "number"},
                    "safeguard_verdict": {"type": "string"},
                },
                "required": ["text", "sentiment_label", "sentiment_score", "safeguard_verdict"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_notification",
            "description": "Send a push notification to the analyst's phone via Pushover when a significant signal is detected.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title":    {"type": "string", "description": "Short alert title."},
                    "message":  {"type": "string", "description": "Alert body text (max 1024 chars)."},
                    "priority": {"type": "integer", "description": "-1=quiet, 0=normal, 1=high, 2=requires confirmation.", "default": 0},
                },
                "required": ["title", "message"],
            },
        },
    },
]


# maps tool name to function

TOOL_REGISTRY: dict[str, callable] = {
    "get_sentiment":    get_sentiment,
    "get_rag_context":  get_rag_context,
    "cross_check":      cross_check,
    "safeguard_check":  safeguard_check,
    "write_brief":      write_brief,
    "store_article":    store_article,
    "send_notification": send_notification,
}


def dispatch(tool_name: str, tool_args: dict) -> str:
    """
    Execute a tool by name and return its result as a JSON string
    (the format Claude expects in the tool result message).
    """
    fn = TOOL_REGISTRY.get(tool_name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        result = fn(**tool_args)
        return json.dumps(result)
    except Exception as exc:                         
        logger.exception("Tool %s failed: %s", tool_name, exc)
        return json.dumps({"error": str(exc)})
