from abc import ABC, abstractmethod


class CrawlerBase(ABC):

    @abstractmethod
    async def crawl(self):
        pass

    @staticmethod
    async def _fetch(session, link):
        try:
            async with session.get(link) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            return e
