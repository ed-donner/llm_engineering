from bs4 import BeautifulSoup
import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

def fetch_website_contents(url):
    try:
        response = requests.get(url=url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        return ""
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "no title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]

def fetch_website_links(url):
    try:
        response = requests.get(url=url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        return ""
    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]