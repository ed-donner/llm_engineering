"""Fetch page title and text after JavaScript has rendered (Playwright).

Same idea as week1/scraper.py, but requests + BeautifulSoup cannot see
React sites such as https://openai.com. Playwright runs Chromium instead.

First time: `uv pip install playwright` then `playwright install chromium`.
"""

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

MAX_CHARS = 2_000


def _text_from_html(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else "No title found"
    if soup.body:
        for tag in soup.body(["script", "style", "img", "input", "nav", "footer"]):
            tag.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return title, text


async def fetch_website_contents(url: str, max_chars: int = MAX_CHARS) -> str:
    """Return title plus visible text, truncated like scraper.py."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()
            # networkidle often hangs on analytics-heavy sites; wait for DOM then JS paint
            await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            await page.wait_for_timeout(2_000)
            html = await page.content()
        finally:
            await browser.close()

    title, text = _text_from_html(html)
    return (title + "\n\n" + text)[:max_chars]


async def fetch_website_links(url: str) -> list[str]:
    """Return hrefs after JavaScript has run."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            await page.wait_for_timeout(2_000)
            hrefs = await page.eval_on_selector_all(
                "a[href]",
                "els => els.map(el => el.getAttribute('href'))",
            )
        finally:
            await browser.close()
    return [href for href in hrefs if href]
