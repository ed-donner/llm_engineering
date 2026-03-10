from bs4 import BeautifulSoup
import requests


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


class Website:
    """Fetches and parses a URL once, exposing title, text contents, and links."""

    def __init__(self, url):
        response = requests.get(url, headers=_HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")

        self.title = soup.title.string if soup.title else "No title found"

        self.links = [a.get("href") for a in soup.find_all("a") if a.get("href")]

        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
        else:
            self.text = ""

    def contents(self, max_chars=2_000):
        return (self.title + "\n\n" + self.text)[:max_chars]


def fetch_website_contents(url):
    """Return the title and contents of the website at the given url; truncated to 2,000 characters."""
    return Website(url).contents()


def fetch_website_links(url):
    """Return the links on the website at the given url."""
    return Website(url).links