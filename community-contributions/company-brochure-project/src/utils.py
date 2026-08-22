"""
utils.py
--------

Small, reusable helper functions shared across the project. Only helpers
that are actually used elsewhere live here.
"""

from __future__ import annotations

import json
from typing import Any


def truncate_text(text: str, max_characters: int) -> str:
    """
    Truncate text to a maximum number of characters.

    Used both when cleaning scraped page content and when assembling the
    final brochure prompt, so the limit logic lives in one place.

    :param text: The text to truncate.
    :param max_characters: Maximum number of characters to keep.
    :return: The truncated text (unchanged if already within the limit).
    """
    return text[:max_characters]


def parse_json_response(raw_response: str) -> dict[str, Any]:
    """
    Parse a JSON string returned by the LLM into a Python dictionary.

    Centralizes JSON parsing so error handling / behavior stays consistent
    everywhere the project needs to interpret a structured LLM response.

    :param raw_response: The raw JSON string returned by the LLM.
    :return: The parsed dictionary.
    :raises json.JSONDecodeError: If the response is not valid JSON.
    """
    return json.loads(raw_response)
