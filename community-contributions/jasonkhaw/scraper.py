from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents(url):
    if not isinstance(url, str):
        return f"[Invalid URL: expected string, got {type(url).__name__}: {repr(url)}]"

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        return f"[Invalid URL schema: {repr(url)}]"

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"[Failed to fetch website contents from {url}: {e}]"

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
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[Failed to fetch website links from {url}: {e}]")
        return []

    soup = BeautifulSoup(response.content, "html.parser")

    links = [link.get("href") for link in soup.find_all("a")]

    return [
        urljoin(url, link)
        for link in links
        if link
    ]