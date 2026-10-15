from bs4 import BeautifulSoup
import requests

def fetch_article(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    paragraphs = soup.find_all("p")
    article = " ".join([p.get_text() for p in paragraphs])

    return article