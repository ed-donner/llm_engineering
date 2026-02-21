"""Utility helpers for ReputationRadar services."""

from __future__ import annotations

import json
import logging
import os
import random
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, TypedDict

from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz


LOG_FILE = Path(__file__).resolve().parents[1] / "logs" / "app.log"
MIN_TEXT_LENGTH = 15
SIMILARITY_THRESHOLD = 90


class NormalizedItem(TypedDict):
    """Canonical representation of a fetched mention."""

    source: str
    id: str
    url: str
    author: Optional[str]
    timestamp: datetime
    text: str
    meta: Dict[str, object]


class ServiceError(RuntimeError):
    """Raised when a service hard fails."""


class ServiceWarning(RuntimeError):
    """Raised for recoverable issues that should surface to the UI."""


def initialize_logger(name: str = "reputation_radar") -> logging.Logger:
    """Configure and return a module-level logger."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


def load_sample_items(name: str) -> List[NormalizedItem]:
    """Load demo data from the samples directory."""
    samples_dir = Path(__file__).resolve().parents[1] / "samples"
    sample_path = samples_dir / f"{name}.json"
    if not sample_path.exists():
        return []
    with sample_path.open("r", encoding="utf-8") as handle:
        raw_items = json.load(handle)
    cleaned: List[NormalizedItem] = []
    for item in raw_items:
        try:
            cleaned.append(
                NormalizedItem(
                    source=item["source"],
                    id=str(item["id"]),
                    url=item.get("url", ""),
                    author=item.get("author"),
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    text=item["text"],
                    meta=item.get("meta", {}),
                )
            )
        except (KeyError, ValueError):
            continue
    return cleaned


def strip_html(value: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    if not value:
        return ""
    soup = BeautifulSoup(value, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
    return text.strip()


def sanitize_text(value: str) -> str:
    """Clean text and remove excessive noise."""
    text = strip_html(value)
    text = re.sub(r"http\S+", "", text)  # drop inline URLs
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def drop_short_items(items: Iterable[NormalizedItem], minimum_length: int = MIN_TEXT_LENGTH) -> List[NormalizedItem]:
    """Filter out items that are too short to analyze."""
    return [
        item
        for item in items
        if len(item["text"]) >= minimum_length
    ]


def fuzzy_deduplicate(items: Sequence[NormalizedItem], threshold: int = SIMILARITY_THRESHOLD) -> List[NormalizedItem]:
    """Remove duplicates based on URL or fuzzy text similarity."""
    seen_urls: set[str] = set()
    deduped: List[NormalizedItem] = []
    for item in items:
        url = item.get("url") or ""
        text = item.get("text") or ""
        if url and url in seen_urls:
            continue
        duplicate_found = False
        for existing in deduped:
            if not text or not existing.get("text"):
                continue
            if fuzz.token_set_ratio(text, existing["text"]) >= threshold:
                duplicate_found = True
                break
        if not duplicate_found:
            deduped.append(item)
            if url:
                seen_urls.add(url)
    return deduped


def normalize_items(items: Sequence[NormalizedItem]) -> List[NormalizedItem]:
    """Apply sanitization, deduplication, and drop noisy entries."""
    sanitized: List[NormalizedItem] = []
    for item in items:
        cleaned_text = sanitize_text(item.get("text", ""))
        if len(cleaned_text) < MIN_TEXT_LENGTH:
            continue
        sanitized.append(
            NormalizedItem(
                source=item["source"],
                id=item["id"],
                url=item.get("url", ""),
                author=item.get("author"),
                timestamp=item["timestamp"],
                text=cleaned_text,
                meta=item.get("meta", {}),
            )
        )
    return fuzzy_deduplicate(sanitized)


def parse_date_range(option: str) -> datetime:
    """Return a UTC timestamp threshold for the given range identifier."""
    now = datetime.now(timezone.utc)
    option = option.lower()
    delta = {
        "24h": timedelta(days=1),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
    }.get(option, timedelta(days=7))
    return now - delta


def random_user_agent() -> str:
    """Return a random user agent string for polite scraping."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/16.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    ]
    return random.choice(user_agents)


def chunked(iterable: Sequence[str], size: int) -> Iterator[Sequence[str]]:
    """Yield successive chunks from iterable."""
    for start in range(0, len(iterable), size):
        yield iterable[start : start + size]


def validate_openai_key(api_key: Optional[str]) -> Tuple[Optional[str], List[str]]:
    """Validate an OpenAI key following the guidance from day1 notebook."""
    warnings: List[str] = []
    if not api_key:
        warnings.append("No OpenAI API key detected. VADER fallback will be used.")
        return None, warnings
    if not api_key.startswith("sk-"):
        warnings.append(
            "Provided OpenAI API key does not start with the expected prefix (sk-)."
        )
    if api_key.strip() != api_key:
        warnings.append("OpenAI API key looks like it has leading or trailing whitespace.")
        api_key = api_key.strip()
    return api_key, warnings


def ensure_timezone(ts: datetime) -> datetime:
    """Guarantee timestamps are timezone-aware in UTC."""
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def safe_int(value: Optional[object], default: int = 0) -> int:
    """Convert a value to int with a fallback."""
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
