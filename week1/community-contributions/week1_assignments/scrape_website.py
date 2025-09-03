from bs4 import BeautifulSoup
import requests


class ScrapeWebsite:

    def __init__(self, url, headers):
        """ Scraping Website which provides title and content"""
        self.url = url
        response = requests.get(self.url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        self.text = soup.body.get_text(separator="\n", strip=True)