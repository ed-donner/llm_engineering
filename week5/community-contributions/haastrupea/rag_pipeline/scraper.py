from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests


HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def get_web_content_sync(url: str, headless: bool = True) -> str:
    """
    Scrape webpage using Playwright sync API (works in Jupyter/Windows).
    Uses requests+BeautifulSoup as fallback if Playwright fails.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page(viewport={"width": 1600, "height": 900})
            page.goto(url)
            body_text = page.inner_text("body")
            browser.close()
            return body_text
    except Exception:
        # Fallback to requests+BeautifulSoup (no browser, works everywhere)
        return fetch_website_contents(url, max_chars=None)




def fetch_website_contents(url: str, max_chars: int = 2_000) -> str:
    """
    Return the title and contents of the website using requests+BeautifulSoup.
    If max_chars is set, truncate to that length. Use max_chars=None for full content.
    """
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    result = title + "\n\n" + text
    return result[:max_chars] if max_chars else result


def fetch_website_links(url):
    """
    Return the links on the webiste at the given url
    I realize this is inefficient as we're parsing twice! This is to keep the code in the lab simple.
    Feel free to use a class and optimize it!
    """
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]
