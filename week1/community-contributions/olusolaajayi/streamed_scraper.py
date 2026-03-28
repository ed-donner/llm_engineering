from bs4 import BeautifulSoup
import requests
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

DEFAULT_TIMEOUT = (20, 120)
MAX_HTML_BYTES = 800_000


def clean_html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else "No title found"

    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input", "noscript"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    return (title + "\n\n" + text)[:2_000]


def fetch_website_contents(url):
    chunks = []
    downloaded = 0

    with requests.get(
        url,
        headers=headers,
        timeout=DEFAULT_TIMEOUT,
        stream=True,
    ) as response:
        response.raise_for_status()
        for piece in response.iter_content(chunk_size=64 * 1024):
            if not piece:
                continue
            chunks.append(piece)
            downloaded += len(piece)
            if downloaded >= MAX_HTML_BYTES:
                break

    content = b"".join(chunks).decode("utf-8", errors="ignore")
    return clean_html_to_text(content)


async def fetch_website_contents_playwright(url, wait_seconds: int = 8):
    timeout_ms = wait_seconds * 1000

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=headers["User-Agent"]
        )

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

            # extra wait for client-side rendering
            await page.wait_for_timeout(3000)

            try:
                await page.wait_for_load_state("networkidle", timeout=timeout_ms)
            except PlaywrightTimeoutError:
                pass

            html = await page.content()
            return clean_html_to_text(html)

        finally:
            await browser.close()