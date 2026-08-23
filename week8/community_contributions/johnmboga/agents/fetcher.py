"""
agents/fetcher.py
Agent 1: RSS Feed Fetcher & Parser
Polls job board RSS feeds and normalises each listing into a
consistent dict with: id, title, company, description, url, date.
"""

import hashlib
import re
import feedparser
from datetime import datetime


class Fetcher:
    """Fetches and parses job listings from RSS feeds."""

    DEFAULT_FEEDS = [
        "https://remoteok.com/remote-jobs.rss",
        "https://weworkremotely.com/remote-jobs.rss",
        "https://feeds.feedburner.com/workatastartup",
    ]

    def __init__(self, default_feeds: list[str] | None = None):
        self._default_feeds = default_feeds or self.DEFAULT_FEEDS

    @staticmethod
    def _clean(text: str) -> str:
        """Strip HTML tags and normalise whitespace."""
        text = re.sub(r"<[^>]+>", " ", text or "")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _make_id(url: str, title: str) -> str:
        """Stable unique ID from URL + title."""
        raw = f"{url}::{title}"
        return hashlib.md5(raw.encode()).hexdigest()

    @staticmethod
    def _extract_company_from_title(title: str) -> str:
        """
        Many RSS feeds encode 'Role at Company' or 'Role - Company' in the title.
        Try to extract the company portion.
        """
        for sep in [" at ", " @ ", " - ", " | "]:
            if sep in title:
                return title.split(sep)[-1].strip()
        return ""

    def _parse_entry(self, entry, feed_url: str) -> dict | None:
        """Extract and normalise a single RSS entry into a job dict."""
        title = self._clean(entry.get("title", ""))
        if not title:
            return None

        url = entry.get("link", feed_url)

        company = (
            entry.get("author")
            or entry.get("dc_creator")
            or entry.get("company")
            or self._extract_company_from_title(title)
            or "Unknown Company"
        )
        company = self._clean(company)

        description = ""
        if entry.get("content"):
            description = self._clean(entry["content"][0].get("value", ""))
        if not description:
            description = self._clean(entry.get("summary", ""))
        if not description:
            description = title

        date = ""
        if entry.get("published"):
            date = entry["published"]
        elif entry.get("updated"):
            date = entry["updated"]

        return {
            "id": self._make_id(url, title),
            "title": title,
            "company": company,
            "description": description[:3000],
            "url": url,
            "date": date,
            "source": feed_url,
        }

    def fetch_jobs(self, feed_urls: list[str] | None = None) -> list[dict]:
        """
        Fetch and parse all jobs from the given RSS feed URLs.
        Returns a list of normalised job dicts.
        """
        feeds = feed_urls or self._default_feeds
        jobs = []

        for url in feeds:
            try:
                parsed = feedparser.parse(url)
                for entry in parsed.entries:
                    job = self._parse_entry(entry, url)
                    if job:
                        jobs.append(job)
            except Exception as e:
                print(f"[Fetcher] Error parsing {url}: {e}")

        return jobs
