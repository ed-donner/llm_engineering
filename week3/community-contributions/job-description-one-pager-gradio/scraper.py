"""Fetch job posting content from a URL. Same pattern as week1 scraper with higher limit for job text."""
from bs4 import BeautifulSoup
import requests

JOB_POST_CHAR_LIMIT = 8_000

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents(url: str, char_limit: int = JOB_POST_CHAR_LIMIT) -> str:
    """Return the title and main text of the page at the given URL."""
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for tag in soup.body(["script", "style", "img", "input", "nav", "footer"]):
            tag.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:char_limit]
