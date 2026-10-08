# this is used for collecting webpage, it fetchs content of this url

import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url
    """
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    for irrelevant in soup.body(["script", "style", "img", "input"]):
        irrelevant.decompose()
    text = soup.body.get_text(separator="\n", strip=True)
    return title + "\n\n" + text