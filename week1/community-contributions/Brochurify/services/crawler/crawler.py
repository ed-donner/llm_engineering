from exceptions import InvalidCrawlType
from .bs4crawler import BS4Crawler


class CrawlerService:
    def __init__(self, url, crawl_type):
        self.crawler = self.crawl_builder(url, crawl_type)

    async def crawl(self):
        await self.crawler.crawl()
        return self.crawler.url_contents

    @staticmethod
    def crawl_builder(url, crawl_type):
        if crawl_type == "normal":
            return BS4Crawler(url)
        raise InvalidCrawlType()

