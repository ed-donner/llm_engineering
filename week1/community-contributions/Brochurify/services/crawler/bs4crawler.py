import aiohttp
import asyncio
from exceptions import BadUrlException
from bs4 import BeautifulSoup
from.__crawler_base import CrawlerBase


class BS4Crawler(CrawlerBase):
    def __init__(self, url):
        self.url = url
        self.visited_links = list()
        self.url_contents = list()

    @staticmethod
    def get_soup_content(soup):
        title = soup.title.string if soup.title else "No title found"
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            text = title + "\t" + soup.body.get_text(separator="\n", strip=True)
            return text
        return ""

    async def main_page_crawl(self, session):
        response = await self._fetch(session, self.url)
        if isinstance(response, BaseException):
            raise BadUrlException()
        soup = BeautifulSoup(response, 'html.parser')

        main_page_text = self.get_soup_content(soup)
        return main_page_text, soup

    async def crawl(self):
        async with aiohttp.ClientSession() as session:
            main_page_text, soup = await self.main_page_crawl(session)
            self.url_contents.append(dict(url=self.url, content=main_page_text))
            self.visited_links.append(self.url)
            links = [link.get('href') for link in soup.find_all('a')]

            requests = list()
            for link in links:
                if link is not None:
                    if link not in self.visited_links and link.startswith(self.url):
                        print(link)
                        requests.append(self.get_url_content(session, link))
                        self.visited_links.append(link)
            print("Starting TO gathering Links")
            if requests:
                responses = await asyncio.gather(*requests, return_exceptions=True)
                for response in responses:
                    if response:
                        self.url_contents.append(response)
            print("Crawling Done")

    async def get_url_content(self, session, link):
        response = await self._fetch(session, link)
        if isinstance(response, BaseException):
            return None
        soup = BeautifulSoup(response, 'html.parser')
        text = self.get_soup_content(soup)
        return dict(url=link, content=text)
