from bs4 import BeautifulSoup
import requests

headers = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_website_contents(url):
    """Return the title and cleaned text of a webpage."""

    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.content, "html.parser")

    title = soup.title.string if soup.title else "No title found"

    for item in soup.body(["script", "style", "img", "input"]):
        item.decompose()

    text = soup.body.get_text(separator="\n", strip=True)

    return title + "\n\n" + text