"""
Searcher Agent: finds current UK PlayStation gift card prices via Tavily.
"""

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Optional: use Tavily if TAVILY_API_KEY is set; otherwise return placeholder for demo
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = bool(os.getenv("TAVILY_API_KEY"))
except ImportError:
    TAVILY_AVAILABLE = False

DEFAULT_QUERY = (
    "PlayStation UK gift card price 2024 2025 CDKeys ShopTo Eneba GAME Amazon"
)


def _tavily_search(query: str, max_results: int = 8) -> str:
    """Run Tavily search and return concatenated snippet text."""
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
        include_answer=True,
    )
    # Tavily can return a dict (e.g. from SDK) or an object; handle both
    if isinstance(response, dict):
        answer = response.get("answer") or ""
        results = response.get("results") or []
    else:
        answer = getattr(response, "answer", None) or ""
        results = getattr(response, "results", []) or []
    parts = []
    if answer and str(answer).strip():
        parts.append(str(answer).strip())
    for r in results:
        if isinstance(r, dict):
            content = (r.get("content") or r.get("snippet") or "").strip()
            url = r.get("url", "")
            if content:
                parts.append(f"[URL: {url}]\n{content}" if url else content)
        else:
            content = (getattr(r, "content", None) or getattr(r, "snippet", None) or "").strip()
            if content:
                parts.append(content)
    return "\n\n".join(parts) if parts else "No results returned."


def searcher_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Node: run Tavily search for UK PlayStation gift card prices.
    Updates state with raw_search_results.
    """
    query = (state.get("search_query") or "").strip() or DEFAULT_QUERY
    if TAVILY_AVAILABLE:
        raw_search_results = _tavily_search(query)
    else:
        raw_search_results = (
            "TAVILY_API_KEY not set. Add it to .env and install: pip install tavily-python\n"
            "Sample: CDKeys £25 PSN UK ~£22.49 (10% off); ShopTo £50 ~£47.99 (4% off)."
        )
    return {"raw_search_results": raw_search_results}
