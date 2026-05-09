"""
Web scraper tool for product discovery.

Fetches a URL, cleans the HTML into readable plain text, and returns
the raw content for an LLM to parse. Keeps this module focused on one job:
get content reliably from any URL.
"""

import re
import time
import logging
from typing import Optional, Dict, Any

import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

_ua = UserAgent()

# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def _build_headers() -> Dict[str, str]:
    """Return browser-like headers with a random user-agent to avoid blocks."""
    return {
        "User-Agent": _ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }


def _fetch_html(url: str, retries: int = 3, timeout: float = 20.0) -> Optional[str]:
    """
    Fetch raw HTML from a URL with retries and exponential back-off.

    Args:
        url: The page URL to fetch.
        retries: How many times to attempt the request before giving up.
        timeout: Per-request timeout in seconds.

    Returns:
        Raw HTML string on success, or None if every attempt fails.
    """
    for attempt in range(1, retries + 1):
        try:
            with httpx.Client(follow_redirects=True, timeout=timeout) as client:
                response = client.get(url, headers=_build_headers())
                response.raise_for_status()
                logger.info("Fetched %s [HTTP %s]", url, response.status_code)
                return response.text
        except httpx.HTTPStatusError as exc:
            logger.warning("HTTP error on attempt %d: %s", attempt, exc)
        except httpx.RequestError as exc:
            logger.warning("Request error on attempt %d: %s", attempt, exc)

        if attempt < retries:
            time.sleep(2 ** attempt)

    logger.error("All %d attempts failed for %s", retries, url)
    return None


# ---------------------------------------------------------------------------
# HTML → plain text
# ---------------------------------------------------------------------------

# Tags whose content adds no product information
_NOISE_TAGS = [
    "script", "style", "noscript", "header", "footer",
    "nav", "aside", "form", "button", "svg", "iframe",
]


def _html_to_text(html: str) -> str:
    """
    Convert raw HTML to clean, compact plain text.

    Removes navigation, scripts, ads, and other non-product noise.
    Collapses excessive blank lines so the output is dense enough to
    fit within an LLM context window.

    Args:
        html: Raw HTML string from the page.

    Returns:
        Plain text string containing only visible, useful content.
    """
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(_NOISE_TAGS):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Collapse runs of blank lines into a single blank line
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace from every line
    lines = [line.strip() for line in text.splitlines()]

    # Drop lines that are empty or contain only punctuation/symbols
    lines = [line for line in lines if len(line) > 2]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scrape_url(url: str) -> str:
    """
    Fetch a URL and return its visible text content.

    This function is intentionally simple: it fetches the page and returns
    the cleaned text. The calling agent (LLM) is responsible for finding,
    filtering, and structuring the product information it needs.

    Args:
        url: Full URL of the page to scrape
             (e.g. "https://www.jumia.co.ke/phones-tablets/?q=phones").

    Returns:
        Plain text content of the page, ready to pass to an LLM.
        Returns an error message string if the fetch fails.
    """
    logger.info("scrape_url called with: %s", url)
    html = _fetch_html(url)

    if html is None:
        return f"ERROR: Could not fetch content from {url}"

    text = _html_to_text(html)
    logger.info("scrape_url returning %d characters of text", len(text))
    return text


# ---------------------------------------------------------------------------
# OpenAI tool schema
# ---------------------------------------------------------------------------

SCRAPE_URL_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "scrape_url",
        "description": (
            "Fetch the visible text content of any webpage URL. "
            "Use this to retrieve product listings from e-commerce sites like Jumia. "
            "Returns the full page text — the caller is responsible for extracting "
            "the relevant product information from it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": (
                        "The full URL of the page to scrape. "
                        "Example: 'https://www.jumia.co.ke/phones-tablets/?q=phones'"
                    ),
                }
            },
            "required": ["url"],
            "additionalProperties": False,
        },
    },
}
