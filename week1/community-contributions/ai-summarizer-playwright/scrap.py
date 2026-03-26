from bs4 import BeautifulSoup
import asyncio
import threading
import sys
import requests
from playwright.async_api import async_playwright


if sys.platform.startswith("win"):
    # Playwright launches a Node subprocess; Proactor loop is required on Windows.
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def _clean_text_from_soup(soup):
    title = soup.title.string.strip() if soup.title and soup.title.string else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return title, text


def _fetch_with_requests(url, timeout=15):
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser")


async def _fetch_with_playwright_async(url, timeout_ms=30000):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent=headers["User-Agent"])
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            await page.wait_for_timeout(1500)
            html = await page.content()
            return BeautifulSoup(html, "html.parser")
        finally:
            await browser.close()


def _fetch_with_playwright(url, timeout_ms=30000):
    try:
        asyncio.get_running_loop()
        loop_running = True
    except RuntimeError:
        loop_running = False

    if not loop_running:
        return asyncio.run(_fetch_with_playwright_async(url, timeout_ms))

    # Jupyter runs an event loop already; run Playwright async code in a thread.
    result = {}
    error = {}

    def _runner():
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


def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit
    """
    try:
        soup = _fetch_with_requests(url)
        title, text = _clean_text_from_soup(soup)
        if len(text) < 500:
            try:
                soup = _fetch_with_playwright(url)
                title, text = _clean_text_from_soup(soup)
            except Exception:
                pass
    except Exception:
        try:
            soup = _fetch_with_playwright(url)
            title, text = _clean_text_from_soup(soup)
        except Exception:
            title, text = "Unable to fetch page", "Both requests and Playwright failed for this URL."
    return (title + "\n\n" + text)[:2_000]


def fetch_website_links(url):
    """
    Return the links on the webiste at the given url
    I realize this is inefficient as we're parsing twice! This is to keep the code in the lab simple.
    Feel free to use a class and optimize it!
    """
    try:
        soup = _fetch_with_requests(url)
    except Exception:
        try:
            soup = _fetch_with_playwright(url)
        except Exception:
            return []
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]
