"""
Job Posting Scraper
====================
Scrapes the text content of a job posting URL, filtering out
nav bars, footers, sidebars, ads, and other irrelevant content.
Returns all relevant text joined into a single string.
"""

import sys
import re
import requests
from bs4 import BeautifulSoup, Comment


# Tags whose entire subtree should be discarded (noise / chrome)
TAGS_TO_REMOVE = {
    "script", "style", "noscript", "iframe", "svg", "canvas",
    "nav", "header", "footer", "aside",
    "form", "input", "button", "select", "textarea",
    "figure", "figcaption", "picture", "img", "video", "audio", "source",
    "link", "meta",
}

# CSS class / id fragments that strongly suggest non-content regions.
# Any element whose class or id contains one of these substrings is dropped.
NOISE_PATTERNS = re.compile(
    r"(nav|navbar|navigation|breadcrumb|menu|sidebar|side-bar|"
    r"footer|header|banner|cookie|gdpr|consent|popup|modal|overlay|"
    r"ad|ads|advert|advertisement|promo|promotion|sponsored|"
    r"social|share|sharing|follow|newsletter|subscribe|signup|sign-up|"
    r"related|recommended|similar|trending|popular|"
    r"pagination|pager|prev|next|back-to-top|scroll-top|"
    r"widget|toolbar|tool-bar|tooltip|flyout|dropdown|"
    r"loading|skeleton|spinner|placeholder)",
    re.IGNORECASE,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _is_noise_element(tag) -> bool:
    """Return True if the element looks like navigation / UI chrome."""
    for attr in ("class", "id", "role", "aria-label"):
        value = tag.get(attr, "")
        if isinstance(value, list):
            value = " ".join(value)
        if value and NOISE_PATTERNS.search(value):
            return True

    # ARIA roles that are structural / chrome
    role = tag.get("role", "")
    if role in {"navigation", "banner", "complementary", "contentinfo",
                "search", "form", "dialog", "alert", "status"}:
        return True

    return False


def fetch_html(url: str) -> str:
    """Download the page HTML."""
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def clean_soup(soup: BeautifulSoup) -> None:
    """Remove all noise elements in-place."""
    # 1. Strip HTML comments
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    # 2. Remove tags that are always noise
    for tag in soup.find_all(TAGS_TO_REMOVE):
        tag.decompose()

    # 3. Remove elements whose attributes suggest they are UI chrome
    for tag in soup.find_all(True):          # True → every element
        if _is_noise_element(tag):
            tag.decompose()


def extract_text(soup: BeautifulSoup) -> str:
    """
    Walk the cleaned tree and collect visible text.
    Returns everything joined into one normalised string.
    """
    # Prefer <main> / <article> if present – they usually wrap job content
    content_root = (
        soup.find("main")
        or soup.find("article")
        or soup.find(id=re.compile(r"(content|job|posting|description)", re.I))
        or soup.find(class_=re.compile(r"(content|job|posting|description)", re.I))
        or soup.body
        or soup
    )

    # Pull all text strings from the chosen root
    texts = []
    for string in content_root.stripped_strings:
        text = string.strip()
        if text:
            texts.append(text)

    # Join with a single space; normalise internal whitespace
    combined = " ".join(texts)
    combined = re.sub(r"\s{2,}", " ", combined)   # collapse multiple spaces
    combined = re.sub(r" ([,\.\!\?\;\:])", r"\1", combined)  # fix space-before-punct
    return combined.strip()


def scrape_job_posting(url: str) -> str:
    """
    Main entry point.
    Fetches the URL, cleans the HTML, and returns all job-related
    text as a single string.
    """
    print(f"[*] Fetching: {url}")
    html = fetch_html(url)

    soup = BeautifulSoup(html, "lxml")

    print("[*] Cleaning page …")
    clean_soup(soup)

    print("[*] Extracting text …")
    text = extract_text(soup)

    return text

