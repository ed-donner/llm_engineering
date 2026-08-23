"""
get_sentiment        — DistilRoberta local classifier
get_rag_context      — ChromaDB semantic search
cross_check          — GPT-4o contrarian analysis
safeguard_check      — GPT-4o JSON safety audit
write_brief          — GPT-4o final investment brief
store_article        — Persist to ChromaDB for future RAG
fetch_news           — Finnhub live news fetch
send_notification    — Pushover phone alert

sentiment and embedding models are hosted on Modal. Fallback to local CPU if MODAL_DEPLOY is set to false.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

import openai
import requests

from config import APP_CONFIG

logger = logging.getLogger(__name__)


_USE_MODAL = os.getenv("MODAL_DEPLOY", "true").lower() != "false"


_seen_article_ids: set[str] = set()

#lazy Modal handles
_modal_sentiment: Any = None
_modal_embedder:  Any = None


def _get_modal_sentiment():
    global _modal_sentiment
    if _modal_sentiment is None:
        import modal
        _modal_sentiment = modal.Cls.from_name(
            "financial-analyst-models", "SentimentModel"
        )
    return _modal_sentiment


def _get_modal_embedder():
    global _modal_embedder
    if _modal_embedder is None:
        import modal
        _modal_embedder = modal.Cls.from_name(
            "financial-analyst-models", "EmbeddingModel"
        )
    return _modal_embedder


#local fallback singletons
_local_sentiment_pipe  = None
_local_embedding_model = None


def _get_local_sentiment_pipe():
    global _local_sentiment_pipe
    if _local_sentiment_pipe is None:
        from transformers import pipeline as hf_pipeline
        logger.info("Loading DistilRoberta locally (Modal disabled)...")
        _local_sentiment_pipe = hf_pipeline(
            "text-classification",
            model=APP_CONFIG.models.sentiment_model,
            truncation=True,
            max_length=512,
        )
    return _local_sentiment_pipe


def _get_local_embedding_model():
    global _local_embedding_model
    if _local_embedding_model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading sentence-transformers locally (Modal disabled)...")
        _local_embedding_model = SentenceTransformer(APP_CONFIG.models.embedding_model)
    return _local_embedding_model



_chroma_collection = None


class _EmbeddingFunction:
    """Routes embeddings to Modal GPU or local CPU."""

    def name(self) -> str:
        return "financial-analyst-embedder"

    def __call__(self, input: list[str]) -> list[list[float]]:  
        return self._embed(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:  
        return self._embed(input)

    def embed_query(self, input: list[str]) -> list[list[float]]: 
        return self._embed(input)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        if _USE_MODAL:
            model = _get_modal_embedder()
            return model().embed.remote(texts)
        model = _get_local_embedding_model()
        return model.encode(texts, show_progress_bar=False).tolist()


def _get_collection():
    global _chroma_collection
    if _chroma_collection is None:
        import chromadb
        from chromadb.config import Settings
        client = chromadb.PersistentClient(
            path=APP_CONFIG.vector_store.persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        _chroma_collection = client.get_or_create_collection(
            name=APP_CONFIG.vector_store.collection_name,
            embedding_function=_EmbeddingFunction(),
            metadata={"hnsw:space": "cosine"},
        )
    return _chroma_collection




def _openai_client() -> openai.OpenAI:
    return openai.OpenAI(api_key=APP_CONFIG.openai_api_key)


#tools

def get_sentiment(text: str) -> dict[str, Any]:
    """
    Classify the financial sentiment of a news article.
    Routes to Modal GPU or local CPU depending on MODAL_DEPLOY.
    """
    if _USE_MODAL:
        model  = _get_modal_sentiment()
        result = model().classify.remote(text)
    else:
        pipe   = _get_local_sentiment_pipe()
        raw    = pipe(text)[0]
        result = {"label": raw["label"].lower(), "score": round(raw["score"], 4)}

    logger.info(
        "[Tool:get_sentiment] %s %.4f (via %s)",
        result["label"], result["score"],
        "Modal" if _USE_MODAL else "local",
    )
    return result


def get_rag_context(text: str) -> dict[str, Any]:
    """
    Retrieve the top-N most semantically similar past articles from ChromaDB.
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
            "text":     results["documents"][0][i][:300],
            "metadata": results["metadatas"][0][i],
            "distance": round(results["distances"][0][i], 4),
        }
        for i in range(len(results["ids"][0]))
    ]
    logger.info("[Tool:get_rag_context] retrieved %d docs", len(articles))
    return {"articles": articles, "count": len(articles)}


def cross_check(article: str, analysis: str) -> dict[str, str]:
    """GPT-4o contrarian / devil's advocate view."""
    client = _openai_client()
    resp   = client.chat.completions.create(
        model=APP_CONFIG.models.gpt_model,
        max_tokens=APP_CONFIG.models.gpt_max_tokens,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a contrarian financial analyst. Challenge the consensus view. "
                    "If bullish find overlooked risks. If bearish find missed opportunities. "
                    "Max 200 words. Be direct."
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
    """GPT-4o audits outputs for hallucinations and unsafe content."""
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
    """GPT-4o writes the final structured investment brief."""
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
                    "**Prior Coverage** (RAG trend, escalation, contradictions, "
                    "or 'First time seeing this story' if none)\n"
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
    """Persist article to ChromaDB for future RAG lookups."""
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


def fetch_news(categories: list[str] = None, limit: int = 20) -> dict[str, Any]:
    """
    Fetch latest financial news from Finnhub across multiple categories.
    Skips articles already seen this session.
    """
    global _seen_article_ids
    categories = categories or ["general", "merger"]

    raw_all: list[dict] = []
    for category in categories:
        try:
            resp = requests.get(
                f"{APP_CONFIG.news.finnhub_base_url}/news",
                params={"category": category},
                headers={"X-Finnhub-Token": APP_CONFIG.finnhub_api_key},
                timeout=10,
            )
            resp.raise_for_status()
            for article in resp.json():
                article["_category"] = category
                raw_all.append(article)
        except requests.RequestException as exc:
            logger.error("Finnhub fetch failed for %s: %s", category, exc)

    raw_all.sort(key=lambda x: x.get("datetime", 0), reverse=True)

    articles: list[dict] = []
    for a in raw_all:
        if not (a.get("headline") and a.get("summary")):
            continue
        article_id = str(a.get("id", ""))
        if article_id and article_id in _seen_article_ids:
            continue
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
            "_category":    a.get("_category", "general"),
        })
        if len(articles) >= limit:
            break

    for a in articles:
        if a["_id"]:
            _seen_article_ids.add(a["_id"])

    logger.info(
        "[Tool:fetch_news] %d new articles from %s (skipped %d, total seen: %d)",
        len(articles), categories,
        len(raw_all) - len(articles),
        len(_seen_article_ids),
    )
    return {"articles": articles, "count": len(articles)}


def send_notification(title: str, message: str, priority: int = 0) -> dict[str, Any]:
    """Send Pushover push notification to analyst's phone."""
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
            "description": (
                "Classify the financial sentiment of a news article using DistilRoberta "
                "(Modal GPU). Returns label (positive/negative/neutral) and confidence score."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The news article text."}
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rag_context",
            "description": (
                "Retrieve semantically similar past articles from ChromaDB. "
                "Use to identify developing stories, sentiment trends, contradictions, "
                "and recurring entities across articles."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The current article text."}
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cross_check",
            "description": "GPT-4o contrarian view to challenge the primary analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "article":  {"type": "string"},
                    "analysis": {"type": "string"},
                },
                "required": ["article", "analysis"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "safeguard_check",
            "description": "Audit for hallucinations, alarmist language, manipulation. Returns PASS/WARN/FAIL.",
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
            "description": "Synthesise all outputs into a structured investment brief with recommendation.",
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
                "required": [
                    "article", "sentiment_label", "sentiment_score",
                    "analysis", "contrarian", "safeguard_verdict", "safeguard_flags",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "store_article",
            "description": "Persist article to ChromaDB for future RAG context.",
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
            "description": "Send Pushover push notification to analyst's phone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title":    {"type": "string"},
                    "message":  {"type": "string"},
                    "priority": {
                        "type": "integer",
                        "description": "-1=quiet, 0=normal, 1=high, 2=requires confirmation.",
                        "default": 0,
                    },
                },
                "required": ["title", "message"],
            },
        },
    },
]


#dispatcher

TOOL_REGISTRY: dict[str, Any] = {
    "get_sentiment":     get_sentiment,
    "get_rag_context":   get_rag_context,
    "cross_check":       cross_check,
    "safeguard_check":   safeguard_check,
    "write_brief":       write_brief,
    "store_article":     store_article,
    "send_notification": send_notification,
}


def dispatch(tool_name: str, tool_args: dict) -> str:
    fn = TOOL_REGISTRY.get(tool_name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        return json.dumps(fn(**tool_args))
    except Exception as exc:              # noqa: BLE001
        logger.exception("Tool %s failed: %s", tool_name, exc)
        return json.dumps({"error": str(exc)})