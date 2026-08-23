from bs4 import BeautifulSoup
import requests
import asyncio

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None


async def fetch_website_contents(url: str) -> str:
    if async_playwright is None:
        return await asyncio.to_thread(fetch_website_contents_jina, url)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)

                html_content = await page.content()

            finally:
                await browser.close()

            soup = BeautifulSoup(html_content, "html.parser")

            title = soup.title.string if soup.title else "No title found"

            if soup.body:
                for irrelevant in soup.body(
                    ["script", "style", "img", "input", "nav", "footer", "noscript"]
                ):
                    irrelevant.decompose()
                text = soup.body.get_text(separator="\n", strip=True)
            else:
                text = ""

            return (title + "\n\n" + text)[:4000]

    except Exception as e:
        print(f"Playwright error fetching {url}: {e}")
        return await asyncio.to_thread(fetch_website_contents_jina, url)


def fetch_website_contents_jina(url: str) -> str:
    """
    An alternative, incredibly robust way to scrape any JS/React site by using Jina's Free Reader API.
    It evaluates JS on its own servers and returns the site content natively in Markdown,
    already cleanly formatted for LLMs!
    """
    jina_url = f"https://r.jina.ai/{url}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    try:
        response = requests.get(jina_url, headers=headers)
        if response.status_code == 200:
            return response.text[:4000]
        return f"Failed to fetch content. Status code: {response.status_code}"
    except Exception as e:
        return f"Error with fallback fetch: {e}"
