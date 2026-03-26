from bs4 import BeautifulSoup
import requests
from playwright.sync_api import sync_playwright


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


def _fetch_with_playwright(url, timeout_ms=30000):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=headers["User-Agent"])
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(1500)
            html = page.content()
            return BeautifulSoup(html, "html.parser")
        finally:
            browser.close()


def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit
    """
    try:
        soup = _fetch_with_requests(url)
        title, text = _clean_text_from_soup(soup)
        if len(text) < 500:
            soup = _fetch_with_playwright(url)
            title, text = _clean_text_from_soup(soup)
    except Exception:
        soup = _fetch_with_playwright(url)
        title, text = _clean_text_from_soup(soup)
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
        soup = _fetch_with_playwright(url)
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]
