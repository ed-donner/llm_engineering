import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


# Use Microsoft Edge that is already installed on Windows, so no need for `playwright install`
# Set to None to use Playwright's own Chromium instead (run `uv run playwright install chromium` first)
BROWSER_CHANNEL = "msedge"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0"


async def _render(url):
    """
    Open the url in a real (headless) browser, let the Javascript run, and return the final HTML
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel=BROWSER_CHANNEL)
        # A headless browser announces itself as "HeadlessEdg" - use a normal user agent instead
        page = await browser.new_page(user_agent=USER_AGENT)
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        try:
            # Sites behind Cloudflare first show a "Just a moment..." check, then redirect to the real page
            await page.wait_for_function("!document.title.includes('Just a moment')", timeout=20_000)
            await page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass  # some sites never go fully idle - just use what has rendered so far
        html = await page.content()
        await browser.close()
    return html


def _render_in_new_loop(url):
    # On Windows, Jupyter uses a "Selector" event loop that can't launch a browser process,
    # so we create our own "Proactor" loop that can
    loop = asyncio.ProactorEventLoop() if sys.platform == "win32" else asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_render(url))
    finally:
        loop.close()


def fetch_html(url):
    """
    Jupyter already has an event loop running, so we run the browser in a separate thread with its own loop
    """
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(_render_in_new_loop, url).result()


def fetch_website_contents(url):
    """
    Same as scraper.fetch_website_contents, but works on Javascript-rendered websites too
    """
    soup = BeautifulSoup(fetch_html(url), "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]


def fetch_website_links(url):
    """
    Same as scraper.fetch_website_links, but works on Javascript-rendered websites too
    """
    soup = BeautifulSoup(fetch_html(url), "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]
