import json
import os
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup


def fetch_url(url):
    """Fetch URL and return raw bytes"""
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    req = Request(url, headers=headers)
    with urlopen(req) as resp:
        return resp.read()

def extract_md_links(url):
    html = fetch_url(url)

    soup = BeautifulSoup(html, "html.parser")

    script = soup.find(
        "script",
        attrs={"data-target": "react-app.embeddedData"}
    )
    if not script:
        raise RuntimeError("Embedded JSON script not found")

    data = json.loads(script.string)

    md_links = []
    for item in data["payload"]["tree"]["items"]:
        if item["contentType"] == "file" and item["name"].endswith(".md"):
            md_links.append(
                "https://raw.githubusercontent.com/python-poetry/poetry/refs/heads/main/"
                + item["path"]
            )

    return md_links

def fetch_urls_as_map(urls):
    result = {}

    for url in urls:
        content = fetch_url(url).decode("utf-8")
        filename = os.path.basename(urlparse(url).path)
        result[filename] = content

    return result
