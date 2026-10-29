import asyncio
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup


# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def _extract_text(html):
    """Extract the title and cleaned body text from raw HTML."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]


def _fetch_with_browser(url, show_browser=False):
    """Render the page in a headless browser to get past bot protection / JS-only sites."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return _fetch_with_browser_sync(url, show_browser)

    # Jupyter already owns an event loop, so run Playwright's sync API in a
    # worker thread with its own synchronous context.
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(_fetch_with_browser_sync, url, show_browser).result()


def _fetch_with_browser_sync(url, show_browser=False):
    """Render a page with Playwright's synchronous API outside an event loop."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not show_browser,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        context = browser.new_context(
            user_agent=headers["User-Agent"],
            locale="nl-BE",
            viewport={"width": 1280, "height": 800},
            extra_http_headers={
                "Accept-Language": "nl-BE,nl;q=0.9,en;q=0.8",
            },
        )
        # Hide the navigator.webdriver flag that headless Chromium exposes
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = context.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=30_000)
            html = page.content()
        finally:
            browser.close()
    return _extract_text(html)


def fetch_website_contents(url, use_browser=False, show_browser=False):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit.

    Set use_browser=True (or let it auto-fallback on a 403) to render the page
    with a headless browser for bot-protected or JavaScript-heavy sites. Set
    show_browser=True to open a visible browser window while fetching.
    """
    if use_browser:
        return _fetch_with_browser(url, show_browser)

    response = requests.get(url, headers=headers)
    if response.status_code == 403:  # bot protection - retry with a real browser
        return _fetch_with_browser(url, show_browser)
    response.raise_for_status()
    return _extract_text(response.content)


def fetch_website_links(url):
    """
    Return the links on the webiste at the given url
    I realize this is inefficient as we're parsing twice! This is to keep the code in the lab simple.
    Feel free to use a class and optimize it!
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]
