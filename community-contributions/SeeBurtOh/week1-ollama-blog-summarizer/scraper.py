"""
Functions for downloading webpage content and discovering links.

This is an enhanced version of the course scraper that returns both
the readable page content and information about links on the page.
"""

from urllib.parse import urldefrag, urljoin

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36"
    )
}


def fetch_page(url, max_chars=5_000):
    """
    Download one webpage.

    Return:
    - The page's final URL
    - The page title
    - Readable text from the page
    - Links found on the page
    """
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20,
    )

    # Raise an exception for responses such as 404 or 500.
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    if soup.title:
        title = soup.title.get_text(" ", strip=True)
    else:
        title = "No title found"

    links = []
    seen_urls = set()

    for anchor in soup.find_all("a", href=True):
        link_text = anchor.get_text(" ", strip=True)

        # Convert links such as "/blog" into full URLs.
        absolute_url = urljoin(response.url, anchor["href"])

        # Remove fragments such as "#about".
        absolute_url = urldefrag(absolute_url).url

        # Ignore mailto:, tel:, javascript:, and similar links.
        if not absolute_url.startswith(("http://", "https://")):
            continue

        if absolute_url in seen_urls:
            continue

        seen_urls.add(absolute_url)

        links.append(
            {
                "text": link_text,
                "url": absolute_url,
                # Many blog platforms put article cards inside
                # an HTML <article> element.
                "inside_article": anchor.find_parent("article") is not None,
            }
        )

    # Remove elements that usually do not contain useful page content.
    for irrelevant in soup.select(
        "script, style, img, input, svg, noscript, form"
    ):
        irrelevant.decompose()

    # Prefer the main page content instead of navigation and footers.
    content = soup.find("main") or soup.body

    if content:
        text = content.get_text(separator="\n", strip=True)
    else:
        text = ""

    return {
        "url": response.url,
        "title": title,
        "text": text[:max_chars],
        "links": links,
    }