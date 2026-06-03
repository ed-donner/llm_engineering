from typing import Optional, List, Set
from openai import OpenAI
from bs4 import BeautifulSoup
from agents.models import ArticleSelection
from agents.agent import Agent
import feedparser
import requests
from concurrent.futures import ThreadPoolExecutor

FEEDS = [
    "https://hnrss.org/newest?points=50&count=15",
    "https://techcrunch.com/feed/",
]

HN_API = "https://hacker-news.firebaseio.com/v0"


class ScannerAgent(Agent):
    name = "Scanner Agent"
    color = Agent.CYAN
    MODEL = "gpt-4.1-mini"

    SYSTEM_PROMPT = (
        "You select the 5 most interesting and impactful tech stories from a list. "
        "Focus on AI, programming, startups, cybersecurity, and major tech developments. "
        "Provide clear 2-3 sentence summaries. Skip promotional content and listicles. "
        "You must include the exact URL from the input for each article."
    )

    def __init__(self):
        self.log("Initializing")
        self.openai = OpenAI()
        self.log("Ready")

    def _fetch_hn_direct(self, limit=10) -> List[str]:
        try:
            ids = requests.get(f"{HN_API}/topstories.json", timeout=10).json()[:limit]
        except Exception:
            return []

        def fetch_one(sid):
            try:
                s = requests.get(f"{HN_API}/item/{sid}.json", timeout=5).json()
                if s and s.get("url"):
                    return (
                        f"Title: {s['title']}\nSummary: (score: {s.get('score', 0)}, "
                        f"{s.get('descendants', 0)} comments)\n"
                        f"Source: Hacker News\nURL: {s['url']}"
                    )
            except Exception:
                pass
            return None

        with ThreadPoolExecutor(max_workers=5) as ex:
            results = list(ex.map(fetch_one, ids))
        return [r for r in results if r]

    def _fetch_rss(self) -> List[str]:
        raw = []
        for feed_url in FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                source = feed.feed.get("title", "RSS")
                for entry in feed.entries[:10]:
                    title = entry.get("title", "")
                    summary = BeautifulSoup(
                        entry.get("summary", ""), "html.parser"
                    ).get_text()[:300]
                    url = entry.get("link", "")
                    raw.append(
                        f"Title: {title}\nSummary: {summary}\n"
                        f"Source: {source}\nURL: {url}"
                    )
            except Exception as e:
                self.log(f"Feed error ({feed_url}): {e}")
        return raw

    def _extract_url(self, entry: str) -> str:
        for line in entry.split("\n"):
            if line.startswith("URL: "):
                return line[5:].strip()
        return ""

    def fetch_articles(self, seen_urls: Set[str]) -> List[str]:
        self.log("Fetching from news feeds")
        raw = self._fetch_rss()
        if len(raw) < 5:
            self.log("RSS sparse, falling back to HN API")
            raw.extend(self._fetch_hn_direct())
        filtered = [r for r in raw if self._extract_url(r) not in seen_urls]
        self.log(f"Found {len(filtered)} new articles (filtered {len(raw) - len(filtered)} seen)")
        return filtered

    def scan(self, seen_urls: Optional[Set[str]] = None) -> Optional[ArticleSelection]:
        raw = self.fetch_articles(seen_urls or set())
        if not raw:
            self.log("No new articles found")
            return None

        user_prompt = (
            "Select the 5 most interesting tech stories from this list. "
            "Include the exact URL from the input.\n\n" + "\n\n".join(raw[:25])
        )
        self.log(f"Asking GPT to select top 5 from {len(raw)} articles (Structured Outputs)")
        result = self.openai.chat.completions.parse(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format=ArticleSelection,
        )
        selection = result.choices[0].message.parsed
        self.log(f"Selected {len(selection.articles)} articles")
        return selection
