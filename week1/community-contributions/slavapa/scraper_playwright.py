"""
Playwright-enhanced website scraper for JavaScript-rendered pages.

Week 1 Day 1 extra exercise — slavapa contribution.
Falls back to requests + BeautifulSoup first; uses Playwright when content is sparse.
Works in plain Python scripts and Jupyter notebooks (including on Windows).
"""

from __future__ import annotations

import asyncio
import sys
import threading

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    )
}

MIN_TEXT_LENGTH = 500
CHAR_LIMIT = 2_000


def _clean_text_from_soup(soup: BeautifulSoup) -> tuple[str, str]:
    title = soup.title.string.strip() if soup.title and soup.title.string else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return title, text


def _fetch_with_requests(url: str, timeout: int = 15) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser")


async def _fetch_with_playwright_async(url: str, timeout_ms: int = 60_000) -> BeautifulSoup:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(user_agent=HEADERS["User-Agent"])
        try:
            await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            await page.wait_for_timeout(1500)
            html = await page.content()
            return BeautifulSoup(html, "html.parser")
        finally:
            await browser.close()


def _fetch_with_playwright(url: str, timeout_ms: int = 60_000) -> BeautifulSoup:
    try:
        asyncio.get_running_loop()
        loop_running = True
    except RuntimeError:
        loop_running = False

    if not loop_running:
        return asyncio.run(_fetch_with_playwright_async(url, timeout_ms))

    result: dict[str, BeautifulSoup] = {}
    error: dict[str, Exception] = {}

    def _runner() -> None:
        try:
            result["soup"] = asyncio.run(_fetch_with_playwright_async(url, timeout_ms))
        except Exception as exc:
            error["exc"] = exc

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()

    if "exc" in error:
        raise error["exc"]
    return result["soup"]


def fetch_website_contents(url: str) -> str:
    """
    Return the title and contents of the website at the given url.
    Uses requests first; falls back to Playwright for JS-heavy sites.
    Truncates to 2,000 characters.
    """
    title, text = "Unable to fetch page", ""

    try:
        soup = _fetch_with_requests(url)
        title, text = _clean_text_from_soup(soup)
        if len(text) < MIN_TEXT_LENGTH:
            soup = _fetch_with_playwright(url)
            title, text = _clean_text_from_soup(soup)
    except Exception:
        try:
            soup = _fetch_with_playwright(url)
            title, text = _clean_text_from_soup(soup)
        except Exception:
            pass

    return (title + "\n\n" + text)[:CHAR_LIMIT]


def fetch_website_links(url: str) -> list[str]:
    """Return href values from anchor tags on the page."""
    try:
        soup = _fetch_with_requests(url)
        title, text = _clean_text_from_soup(soup)
        if len(text) < MIN_TEXT_LENGTH:
            soup = _fetch_with_playwright(url)
    except Exception:
        try:
            soup = _fetch_with_playwright(url)
        except Exception:
            return []

    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]
