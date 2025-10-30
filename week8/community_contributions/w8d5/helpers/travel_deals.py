from pydantic import BaseModel
from typing import List, Dict, Self
from bs4 import BeautifulSoup
import re
import feedparser
from tqdm import tqdm
import requests
import time

feeds = [
    "https://thepointsguy.com/feed/",
]

def extract(html_snippet: str) -> str:
    soup = BeautifulSoup(html_snippet, 'html.parser')
    text = soup.get_text(strip=True)
    text = re.sub('<[^<]+?>', '', text)
    return text.replace('\n', ' ').strip()

class ScrapedTravelDeal:
    title: str
    summary: str
    url: str
    details: str

    def __init__(self, entry: Dict[str, str]):
        self.title = entry.get('title', '')
        summary_text = entry.get('summary', entry.get('description', ''))
        self.summary = extract(summary_text)
        self.url = entry.get('link', '')
        self.details = self.summary

    def __repr__(self):
        return f"<{self.title}>"

    def describe(self):
        return f"Title: {self.title}\nDetails: {self.details.strip()}\nURL: {self.url}"

    @classmethod
    def fetch(cls, show_progress: bool = False) -> List[Self]:
        deals = []
        feed_iter = tqdm(feeds) if show_progress else feeds
        for feed_url in feed_iter:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:10]:
                    deals.append(cls(entry))
                    time.sleep(0.3)
            except Exception as e:
                print(f"Error fetching {feed_url}: {e}")
        return deals

class TravelDeal(BaseModel):
    destination: str
    deal_type: str
    description: str
    price: float
    url: str

class TravelDealSelection(BaseModel):
    deals: List[TravelDeal]

class TravelOpportunity(BaseModel):
    deal: TravelDeal
    estimate: float
    discount: float

