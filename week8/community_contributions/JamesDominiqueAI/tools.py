"""
tools.py
--------
Tool definitions sent to the Anthropic API and any local helper utilities.

The web_search tool is a *hosted* Anthropic tool — we declare it here and
the API executes it on our behalf.  No scraping credentials needed.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


# ── Tool Schemas ─────────────────────────────────────────────────────────────

WEB_SEARCH_TOOL: dict[str, Any] = {
    "type": "web_search_20250305",
    "name": "web_search",
}

ALL_TOOLS: list[dict[str, Any]] = [WEB_SEARCH_TOOL]


# ── Tool-use Event Parser ─────────────────────────────────────────────────────

class ToolEvent:
    """Lightweight representation of a tool-use or tool-result block."""

    def __init__(self, block: dict[str, Any]):
        self.type: str = block.get("type", "")
        self.name: str = block.get("name", "")
        self.tool_use_id: str = block.get("id", block.get("tool_use_id", ""))
        self.input: dict = block.get("input", {})
        self.content: Any = block.get("content", "")

    # ── helpers ──
    @property
    def is_tool_use(self) -> bool:
        # server-side web_search returns type "tool_use" or "server_tool_use"
        return self.type in ("tool_use", "server_tool_use")

    @property
    def is_web_search(self) -> bool:
        return self.is_tool_use and self.name == "web_search"

    @property
    def search_query(self) -> str:
        return self.input.get("query", "")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ToolEvent type={self.type!r} name={self.name!r}>"


def parse_tool_events(content_blocks: list[dict]) -> list[ToolEvent]:
    """Convert raw API content blocks into ToolEvent objects."""
    return [ToolEvent(b) for b in content_blocks]


def build_tool_result_messages(content_blocks: list[dict]) -> list[dict] | None:
    """
    When stop_reason == 'tool_use', the API expects us to return a user message
    containing tool_result blocks for every tool_use block.

    For the hosted web_search tool the API handles execution itself, so we
    return a minimal acknowledgement that keeps the conversation loop alive.
    """
    tool_uses = [b for b in content_blocks if b.get("type") == "tool_use"]
    if not tool_uses:
        return None

    tool_results = [
        {
            "type": "tool_result",
            "tool_use_id": tu["id"],
            "content": "Search executed successfully.",
        }
        for tu in tool_uses
    ]
    return [{"role": "user", "content": tool_results}]


def extract_text_blocks(content_blocks: list[dict]) -> str:
    """Concatenate all text-type blocks from a response."""
    return "\n".join(
        b.get("text", "") for b in content_blocks if b.get("type") == "text"
    )


def safe_json(obj: Any) -> str:
    """Best-effort JSON serialisation for logging."""
    try:
        return json.dumps(obj, indent=2, default=str)
    except Exception:
        return str(obj)
