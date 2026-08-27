from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import requests


# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit
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
    return (title + "\n\n" + text)[:2_000]
    
def fetch_website_links(url):
    """
    Return valid absolute links found on the website at the given URL.

    Relative links such as '/models' are converted into absolute URLs,
    such as 'https://huggingface.co/models'.
    """

    response = requests.get(
        url,
        headers=headers,
        timeout=15,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    links = []

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()

        if not href:
            continue

        # Ignore links that cannot be fetched as web pages.
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        absolute_url = urljoin(url, href)

        parsed_url = urlparse(absolute_url)

        if parsed_url.scheme not in {"http", "https"}:
            continue

        links.append(absolute_url)

    # Remove duplicates while preserving the original order.
    return list(dict.fromkeys(links))