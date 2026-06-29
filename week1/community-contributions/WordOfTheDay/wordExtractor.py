from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup


WORD_OF_THE_DAY_URL = "https://www.vocabulary.com/word-of-the-day/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}


def fetch_word_of_the_day(url) -> dict[str, str]:
    """
    Fetch Vocabulary.com's word of the day.

    Returns:
        A dictionary with the word, meaning, usage, date, and source URL.
    """
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    word = _extract_word(soup)
    usage, meaning = _extract_usage_and_meaning(soup, word)
    date = _extract_date(soup)

    return {
        "word": word,
        "meaning": meaning,
        "usage": usage,
        "date": date,
        "source": url,
    }


def _extract_word(soup: BeautifulSoup) -> str:
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    title_match = re.search(r"Word of the day:\s*(.+?)\s*\|", title, re.I)
    if title_match:
        return title_match.group(1).strip()

    heading = soup.find(string=re.compile(r"^\s*word of the day\s*$", re.I))
    if heading:
        for link in heading.find_all_next("a"):
            text = link.get_text(" ", strip=True)
            if _looks_like_word(text):
                return text

    raise ValueError("Could not find the word of the day on the page.")


def _extract_usage_and_meaning(soup: BeautifulSoup, word: str) -> tuple[str, str]:
    word_link = soup.find("a", string=lambda text: text and text.strip() == word)
    if word_link:
        paragraphs = []
        for tag in word_link.find_all_next(["p", "a", "h2", "h3", "hr"]):
            if tag.name == "p":
                text = tag.get_text(" ", strip=True)
                if text:
                    paragraphs.append(text)
                continue

            if paragraphs:
                break

        if len(paragraphs) >= 2:
            return paragraphs[0], paragraphs[1]

    page_text = soup.get_text("\n", strip=True)
    match = re.search(
        rf"\b{re.escape(word)}\b\s*\n+(.+?)(?:\n+SEE FULL DEFINITION|\n+\* \* \*)",
        page_text,
        re.I | re.S,
    )
    if match:
        paragraphs = [
            paragraph.strip()
            for paragraph in re.split(r"\n\s*\n", match.group(1))
            if paragraph.strip()
        ]
        if len(paragraphs) >= 2:
            usage = re.sub(r"\s*\n\s*", " ", paragraphs[0]).strip()
            meaning = re.sub(r"\s*\n\s*", " ", paragraphs[1]).strip()
            return usage, meaning

    raise ValueError("Could not find the usage and meaning on the page.")


def _extract_date(soup: BeautifulSoup) -> str:
    page_text = soup.get_text("\n", strip=True)
    match = re.search(
        r"\b(?:January|February|March|April|May|June|July|August|September|"
        r"October|November|December)\s+\d{1,2},\s+\d{4}\b",
        page_text,
    )
    return match.group(0) if match else ""


def _looks_like_word(text: str) -> bool:
    lowered = text.lower()
    rejected = {
        "dictionary",
        "vocabulary lists",
        "vocabtrainer",
        "previous word of the day",
        "next word of the day",
    }
    return bool(text) and lowered not in rejected and len(text.split()) <= 4

