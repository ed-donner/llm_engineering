from __future__ import annotations

from typing import List, Tuple
import requests
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    )
}


def fetch_website_contents(url: str, headers: dict | None = None, max_chars: int = 2_000) -> str:
    response = requests.get(url, headers=headers or DEFAULT_HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input", "noscript"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:max_chars]


def fetch_website_links(url: str, headers: dict | None = None) -> List[str]:
    response = requests.get(url, headers=headers or DEFAULT_HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    return [a.get("href") for a in soup.find_all("a") if a.get("href")]

