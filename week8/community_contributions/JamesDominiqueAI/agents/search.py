"""
agents/search.py
----------------
Shared web search executor for GPT-4o and Gemini agents.
Uses DuckDuckGo — free, no API key required.

The tool schema is defined here in OpenAI function-calling format,
which works for both OpenAI (GPT-4o) and OpenRouter (Gemini).
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Tool Schema (OpenAI function-calling format) ──────────────────────────────

WEB_SEARCH_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for current, real-time information on any topic. "
            "Use this to find recent data, news, statistics, and expert analysis."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string",
                }
            },
            "required": ["query"],
        },
    },
}

ALL_TOOLS = [WEB_SEARCH_TOOL]


# ── Executor ──────────────────────────────────────────────────────────────────

def execute_search(query: str, max_results: int = 6) -> str:
    """
    Execute a DuckDuckGo web search and return formatted results as a string.
    Falls back gracefully if the library is unavailable.
    """
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                title   = r.get("title", "")
                href    = r.get("href", "")
                snippet = r.get("body", "")
                results.append(f"**{title}**\n{href}\n{snippet}")

        if not results:
            return f"No results found for: {query}"

        logger.info("[Search] query=%r results=%d", query, len(results))
        return "\n\n---\n\n".join(results)

    except ImportError:
        logger.warning("[Search] duckduckgo_search not installed — returning placeholder")
        return f"[Search unavailable] Query was: {query}"
    except Exception as exc:
        logger.warning("[Search] DuckDuckGo error for %r: %s", query, exc)
        return f"Search error for '{query}': {exc}"


def parse_tool_calls(message) -> list[dict]:
    """Extract tool_calls from an OpenAI chat completion message."""
    if not hasattr(message, "tool_calls") or not message.tool_calls:
        return []
    calls = []
    for tc in message.tool_calls:
        try:
            args = json.loads(tc.function.arguments)
        except (json.JSONDecodeError, AttributeError):
            args = {}
        calls.append({
            "id":    tc.id,
            "name":  tc.function.name,
            "args":  args,
        })
    return calls


def build_tool_result_messages(tool_calls: list[dict]) -> list[dict]:
    """
    Execute each tool call and return the tool-result messages
    to append to the conversation before the next API call.
    """
    messages = []
    for tc in tool_calls:
        if tc["name"] == "web_search":
            query  = tc["args"].get("query", "")
            result = execute_search(query)
        else:
            result = f"Unknown tool: {tc['name']}"

        messages.append({
            "role":         "tool",
            "tool_call_id": tc["id"],
            "content":      result,
        })
    return messages
