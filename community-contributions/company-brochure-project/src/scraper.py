"""
scraper.py
----------

Responsible only for the raw web-scraping mechanics of the project:

* issuing HTTP requests
* parsing HTML with BeautifulSoup
* cleaning page content (removing scripts, styles, images, forms/inputs)
* extracting the title + body text of a page
* extracting the list of links found on a page

No LLM logic, prompt logic, or brochure-assembly logic lives here.
"""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup

from utils import truncate_text

# ==========================
# Constants
# ==========================

# Standard browser-like headers so sites don't reject a "bot" user agent.
REQUEST_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    )
}

# Sensible timeout (in seconds) so a hanging request never blocks forever.
REQUEST_TIMEOUT_SECONDS: int = 15

# Same truncation limit used in the original notebook/scraper.py.
MAX_CONTENT_CHARACTERS: int = 2_000

# Tags considered irrelevant to the textual content of a page.
IRRELEVANT_TAGS: tuple[str, ...] = ("script", "style", "img", "input")

DEFAULT_TITLE: str = "No title found"


def fetch_website_contents(url: str) -> str:
    """
    Fetch a URL and return its cleaned title + body text.

    Scripts, styles, images, and form inputs are stripped out before the
    text is extracted. The result is truncated to MAX_CONTENT_CHARACTERS,
    matching the original notebook behavior.

    :param url: Full URL of the page to fetch.
    :return: A string of the form "<title>\n\n<body text>", truncated.
    """
    response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    title = soup.title.string if soup.title else DEFAULT_TITLE

    if soup.body:
        for irrelevant in soup.body(IRRELEVANT_TAGS):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""

    contents = f"{title}\n\n{text}"
    return truncate_text(contents, MAX_CONTENT_CHARACTERS)


def fetch_website_links(url: str) -> list[str]:
    """
    Fetch a URL and return the list of href values found on the page.

    Note: this re-fetches/re-parses the page independently of
    fetch_website_contents. This mirrors the original (intentionally
    simple) notebook implementation, which parses the page twice rather
    than sharing a single BeautifulSoup object.

    :param url: Full URL of the page to fetch.
    :return: A list of non-empty href strings (may be relative or absolute).
    """
    response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]

    return [link for link in links if link]
