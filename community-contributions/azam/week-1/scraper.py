"""Lightweight website scraper used by the week-1 notebooks.

Fetches a page over HTTP and returns a clean, text-only representation
(title + visible body text) that is suitable for feeding into an LLM prompt.
"""

import requests
from bs4 import BeautifulSoup

# Pretend to be a real browser so sites don't block the request with a 403.
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

IRRELEVANT_TAGS = ["script", "style", "img", "input"]


def clean_html(html: str | bytes) -> str:
    """Strip a raw HTML document down to its title and visible text.

    Removes scripts, styles, images and form inputs, then collapses the
    remaining DOM into newline-separated, trimmed text. Use this to turn any
    HTML source (from `requests`, Selenium, a file, ...) into a compact,
    token-friendly string suitable for an LLM prompt.

    Args:
        html: The raw HTML markup to clean.

    Returns:
        The page title followed by its cleaned, visible text.
    """
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string if soup.title else "No title found"

    for irrelevant_tag in soup(IRRELEVANT_TAGS):
        irrelevant_tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return f"Title: {title}\n\n{text}"


def fetch_website_content(url: str) -> str:
    """Fetch a website and return its title and visible text as a single string.

    Args:
        url: The URL of the website to fetch.

    Returns:
        The page title followed by its cleaned, visible text. On failure,
        returns a human-readable error string instead of raising.
    """
    try:
        response = requests.get(url=url, headers=headers, timeout=10)
        response.raise_for_status()  
        return clean_html(response.content)
    except Exception as e:
        return f"Error fetching content from {url}: {str(e)}"
