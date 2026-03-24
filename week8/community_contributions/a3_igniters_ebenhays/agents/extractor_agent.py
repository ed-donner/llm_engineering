import urllib.parse
import requests
from bs4 import BeautifulSoup
from newspaper import Article

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


class ArticleExtractorAgent:
    """Resolves and extracts the full text of a news article.

    Google News RSS links point to Google's own redirect pages, not the
    publisher directly. This agent resolves the real URL by running a
    DuckDuckGo site-search using the article title and publisher domain,
    then extracts the article text using newspaper3k with a BeautifulSoup
    fallback.
    """

    def __init__(self, title: str, source_url: str):
        self.title = title
        self.source_url = source_url
        self.url = self._resolve_url()

    def _resolve_url(self) -> str:
        """Use DuckDuckGo HTML search to find the real article URL."""
        try:
            domain = urllib.parse.urlparse(self.source_url).netloc or self.source_url
            query = f"site:{domain} {self.title[:80]}"
            ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
            resp = requests.get(ddg_url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for anchor in soup.select(".result__a"):
                href = anchor.get("href", "")
                # DuckDuckGo wraps URLs in its own redirect; decode the uddg param
                parsed = urllib.parse.urlparse(href)
                params = urllib.parse.parse_qs(parsed.query)
                real_url = params.get("uddg", [None])[0]
                if real_url and domain in real_url:
                    return urllib.parse.unquote(real_url)
        except Exception as e:
            print(f"URL resolution error for '{self.title}': {e}")
        # Fall back to the publisher home page so at least the domain is correct
        return self.source_url

    def _fallback_extract(self) -> str | None:
        """BeautifulSoup paragraph extractor when newspaper3k fails."""
        try:
            resp = requests.get(self.url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
            text = "\n\n".join(p for p in paragraphs if p)
            return text[:4000] if text else None
        except Exception as e:
            print(f"Fallback extractor error for {self.url}: {e}")
            return None

    def extract(self) -> str | None:
        try:
            article = Article(self.url)
            article.download()
            article.parse()
            text = article.text
            if text and text.strip():
                return text[:4000]
        except Exception as e:
            print(f"Newspaper extractor error for {self.url}: {e}")

        return self._fallback_extract()
