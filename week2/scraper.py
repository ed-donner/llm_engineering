from bs4 import BeautifulSoup
import requests
import re
from playwright.sync_api import sync_playwright
import asyncio
import json



# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url;
    truncate to 10,000 characters as a sensible limit
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:10_000]


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

def render_page(url, timeout=20):
    """Render dynamic pages using Playwright (synchronous)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=headers["User-Agent"])
        page.goto(url, timeout=timeout * 1000, wait_until="networkidle")
        html = page.content()
        browser.close()
        return html

def extract_visible_text(html):
    """Extract visible, meaningful text from HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove irrelevant elements
    for tag in soup(["script", "style", "img", "noscript", "footer", "header",
                     "nav", "aside", "iframe", "input", "button", "svg", "form"]):
        tag.decompose()

    text_blocks = []
    for tag in soup.find_all(["p", "li", "div", "section", "article"]):
        txt = tag.get_text(" ", strip=True)
        if len(txt.split()) > 8 and not re.search(
            r"cookies|impressum|datenschutz|privacy|subscribe", txt, re.I
        ):
            text_blocks.append(txt)

    combined = "\n\n".join(dict.fromkeys(text_blocks))  # deduplicate preserving order
    combined = re.sub(r"\n{2,}", "\n\n", combined)
    return combined.strip()

def extract_job_posting(url):
    """End-to-end: render → extract text → detect language → parse via LLM."""
    print(f"Fetching: {url}")
    html = render_page(url)
    text = extract_visible_text(html)
    #lang = detect_language(text)
    #print(f"Detected language: {lang}")
    #result = extract_with_llm(text, lang)
    return text        