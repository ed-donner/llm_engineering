"""
Valuer Agent: GPT-4o with specialist system prompt (simulates fine-tuned pricing expertise).
Rule: PlayStation UK cards usually 5–10% discount; >12% = Strong Buy.
"""

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# Import from project root (damola-adewunmi)
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
from prompts import VALUER_SYSTEM_PROMPT, VALUER_USER_TEMPLATE


def _parse_valuer_response(text: str) -> list[dict]:
    """Extract JSON from model output; return list of deals or empty list."""
    text = (text or "").strip()
    # Try to find JSON block
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return []
    try:
        data = json.loads(match.group())
        return data.get("deals", []) if isinstance(data, dict) else []
    except json.JSONDecodeError:
        return []


def valuer_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Node: run GPT-4o with specialist prompt on raw_search_results.
    Outputs structured valued_deals (retailer, denomination, price, discount_pct, verdict, url).
    """
    raw = state.get("raw_search_results") or ""
    if not raw.strip():
        return {"valued_deals": []}

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    messages = [
        SystemMessage(content=VALUER_SYSTEM_PROMPT),
        HumanMessage(content=VALUER_USER_TEMPLATE.format(search_results=raw)),
    ]
    response = llm.invoke(messages)
    content = response.content if hasattr(response, "content") else str(response)
    valued_deals = _parse_valuer_response(content)
    return {"valued_deals": valued_deals}
