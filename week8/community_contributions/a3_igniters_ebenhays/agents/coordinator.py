from typing import Generator
from agents.category_agent import CategoryAgent
from agents.extractor_agent import ArticleExtractorAgent
from agents.summarizer_agent import SummarizerAgent


class NewsCoordinator:

    def __init__(self, categories):
        self.categories = categories

    def run(self):
        all_results = []
        for category in self.categories:
            print(f"\nFetching {category} news...\n")
            agent = CategoryAgent(category)
            results = agent.run()
            all_results.extend(results)
        return all_results

    def stream(self) -> Generator[dict, None, None]:
        """Yield article dicts one by one as they are processed.

        Yields status sentinel dicts (type='status') followed by article dicts
        (type='article') so the UI can display live progress.
        """
        for category in self.categories:
            yield {
                "type": "status",
                "category": category,
                "message": f"Searching {category} news...",
            }
            agent = CategoryAgent(category)
            articles_raw = agent.search_news()
            if not articles_raw:
                yield {
                    "type": "status",
                    "category": category,
                    "message": f"No articles found for '{category}'.",
                }
                continue

            yield {
                "type": "status",
                "category": category,
                "message": f"Found {len(articles_raw)} article(s) — extracting & summarising...",
            }

            for article_meta in articles_raw:
                if not article_meta.get("title") or not article_meta.get("source_url"):
                    continue

                extractor = ArticleExtractorAgent(
                    article_meta["title"], article_meta["source_url"]
                )
                content = extractor.extract()
                if not content:
                    continue
                summarizer = SummarizerAgent()
                summary = summarizer.summarize(content)
                yield {
                    "type": "article",
                    "category": category,
                    "title": article_meta["title"],
                    "summary": summary,
                    "url": extractor.url,
                }
