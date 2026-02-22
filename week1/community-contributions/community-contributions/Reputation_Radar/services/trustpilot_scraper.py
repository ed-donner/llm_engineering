"""Trustpilot scraping service with polite crawling safeguards."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, List
from urllib.parse import urlencode
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .utils import (
    NormalizedItem,
    ServiceError,
    ServiceWarning,
    ensure_timezone,
    random_user_agent,
    sanitize_text,
)

BASE_URL = "https://www.trustpilot.com"
SEARCH_PATH = "/search"


class BlockedError(ServiceWarning):
    """Raised when Trustpilot blocks the scraping attempt."""


def _check_robots(user_agent: str) -> None:
    parser = RobotFileParser()
    parser.set_url(f"{BASE_URL}/robots.txt")
    parser.read()
    if not parser.can_fetch(user_agent, SEARCH_PATH):
        raise ServiceWarning(
            "Trustpilot robots.txt disallows scraping the search endpoint. "
            "Please use the official API or upload data manually."
        )


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((requests.RequestException, BlockedError)),
)
def _fetch_page(session: requests.Session, user_agent: str, page: int, brand: str, language: str) -> str:
    params = {"query": brand, "page": page}
    if language:
        params["languages"] = language
    url = f"{BASE_URL}{SEARCH_PATH}?{urlencode(params)}"
    response = session.get(
        url,
        headers={"User-Agent": user_agent, "Accept-Language": language or "en"},
        timeout=20,
    )
    if response.status_code in (401, 403):
        raise BlockedError("Trustpilot denied access (HTTP 403).")
    response.raise_for_status()
    return response.text


def _parse_reviews(html: str, user_agent: str) -> List[NormalizedItem]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("article[data-service-review-card-layout]")
    items: List[NormalizedItem] = []
    now = datetime.now(timezone.utc)
    for card in cards:
        link = card.select_one("a.link_internal__YpiJI")
        url = f"{BASE_URL}{link['href']}" if link and link.get("href") else ""
        title_el = card.select_one("h2")
        title = title_el.get_text(strip=True) if title_el else ""
        text_el = card.select_one("[data-review-description-typography]")
        text = text_el.get_text(separator=" ", strip=True) if text_el else ""
        rating_el = card.select_one("img[alt*='stars']")
        rating = rating_el["alt"] if rating_el and rating_el.get("alt") else ""
        author_el = card.select_one("span.styles_consumerDetails__ZF4I6")
        author = author_el.get_text(strip=True) if author_el else None
        date_el = card.select_one("time")
        timestamp = now
        if date_el and date_el.get("datetime"):
            try:
                timestamp = datetime.fromisoformat(date_el["datetime"].replace("Z", "+00:00"))
            except ValueError:
                timestamp = now

        body = sanitize_text(f"{title}\n\n{text}")
        if len(body) < 15:
            continue
        items.append(
            NormalizedItem(
                source="trustpilot",
                id=card.get("data-review-id", str(hash(body))),
                url=url,
                author=author,
                timestamp=ensure_timezone(timestamp),
                text=body,
                meta={
                    "rating": rating,
                    "user_agent": user_agent,
                },
            )
        )
    return items


def fetch_reviews(brand: str, language: str = "en", pages: int = 2) -> List[NormalizedItem]:
    """Scrape Trustpilot search results for recent reviews."""
    if not brand:
        raise ServiceWarning("Brand name is required for Trustpilot scraping.")

    session = requests.Session()
    user_agent = random_user_agent()
    _check_robots(user_agent)

    aggregated: List[NormalizedItem] = []
    seen_ids: set[str] = set()

    for page in range(1, pages + 1):
        try:
            html = _fetch_page(session, user_agent=user_agent, page=page, brand=brand, language=language)
        except BlockedError as exc:
            raise ServiceWarning(
                "Trustpilot blocked the scraping attempt. Consider using their official API or providing CSV uploads."
            ) from exc
        except requests.RequestException as exc:  # noqa: BLE001
            raise ServiceError(f"Trustpilot request failed: {exc}") from exc
        page_items = _parse_reviews(html, user_agent)
        for item in page_items:
            if item["id"] in seen_ids:
                continue
            aggregated.append(item)
            seen_ids.add(item["id"])
        time.sleep(1.5)  # gentle crawl delay

    return aggregated
