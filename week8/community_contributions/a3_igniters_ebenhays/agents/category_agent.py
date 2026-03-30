import urllib.parse
import requests
import xml.etree.ElementTree as ET
from agents.extractor_agent import ArticleExtractorAgent
from agents.summarizer_agent import SummarizerAgent
from typing import List, Dict


class CategoryAgent:

    def __init__(self, category):
        self.category = category
        self.MAX_ARTICLES_PER_CATEGORY = 2

    def search_news(self) -> List[Dict[str, str]]:
        """Fetch Google News RSS for the category.

        Google News RSS <link> elements point to Google's own redirect pages, not
        the publisher's article URLs directly. We also capture the <source url="...">
        attribute which contains the publisher's base domain so the extractor can
        resolve the real article URL via a DuckDuckGo site-search.
        """
        print(f"Searching news for category: {self.category}")
        query = urllib.parse.quote_plus(self.category)
        url: str = f"https://news.google.com/rss/search?q={query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; NewsFetcher/1.0; +https://example.com)"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            items = root.findall(".//item")[: self.MAX_ARTICLES_PER_CATEGORY]
            articles: List[Dict[str, str]] = []
            for item in items:
                title = item.findtext("title") or ""
                # Strip the trailing " - Publisher Name" from the title
                title = title.rsplit(" - ", 1)[0].strip() if " - " in title else title
                source_el = item.find("source")
                source_url = source_el.get("url", "") if source_el is not None else ""
                if title and source_url:
                    articles.append({"title": title, "source_url": source_url})
            return articles
        except Exception:
            return []

    def run(self):
        """Main entry point for the CategoryAgent."""
        articles: List[Dict[str, str]] = self.search_news()
        if not articles:
            return []
        results: List[Dict[str, str]] = []
        for article in articles:
            if not article.get("title") or not article.get("source_url"):
                continue
            extractor = ArticleExtractorAgent(article["title"], article["source_url"])
            content = extractor.extract()
            if not content:
                continue
            summarizer = SummarizerAgent()
            summary = summarizer.summarize(content)
            results.append(
                {
                    "category": self.category,
                    "title": article["title"],
                    "summary": summary,
                    "url": extractor.url,
                }
            )
        return results
