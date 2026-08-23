from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import asyncio

# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


async def get_rendered_html(url):
    """
    Use Playwright to fetch the fully rendered HTML of a page.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent=headers["User-Agent"])
        try:
            # page.goto(url, timeout=15000) # 15 second timeout
            await page.goto(url, timeout=30000, wait_until='networkidle')
            await page.wait_for_selector('body', state='visible', timeout=30000)
            html = await page.content()
            # A simple wait to let some JS render, might need to be more specific for complex sites
            # await page.wait_for_timeout(2000)
        finally:
            await browser.close()
    return html


async def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url,
    using Playwright to handle JavaScript-rendered pages.
    Truncates to 2,000 characters as a sensible limit.
    """
    html = await get_rendered_html(url)
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input", "nav", "footer", "header"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]


async def fetch_website_links(url):
    """
    Return the links on the website at the given url,
    using Playwright to handle JavaScript-rendered pages.
    """
    html = await get_rendered_html(url)
    soup = BeautifulSoup(html, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link and link.startswith('http')]
