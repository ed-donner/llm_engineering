import requests
from bs4 import BeautifulSoup


class Scraper:
    def __init__(self, url):
        self.headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        }
        self.url=url
        self.response=requests.get(url=url, headers=self.headers)
        assert self.response.status_code == 200, f"Unable to fetch content from {url}"

    def get_content(self):
        html_content = self.response.text
        soup = BeautifulSoup(html_content, "html.parser")
        page_content=f"Title: {soup.title.text or "No Title" }"
        for paragraph in soup.find_all("p"):
            page_content+=f"\n {paragraph.text}"
        return page_content
    def get_links(self):
        soup = BeautifulSoup(self.response.content, "html.parser")
        links = [link.get("href") for link in soup.find_all("a")]
        return [link for link in links if link]



content = Scraper("https://sajjadjonayed.com")
print(content.get_links())
