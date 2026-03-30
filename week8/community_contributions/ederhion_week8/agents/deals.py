from pydantic import BaseModel, Field
from typing import List, Dict
from bs4 import BeautifulSoup
import re
import feedparser
from tqdm import tqdm
import requests
import time

# Point to an automotive-specific Really Simple Syndication (RSS) feed
feeds = [
    "https://www.dealnews.com/c238/Automotive/?rss=1",
]

def extract(html_snippet: str) -> str:
    soup = BeautifulSoup(html_snippet, "html.parser")
    snippet_div = soup.find("div", class_="snippet summary")

    if snippet_div:
        description = snippet_div.get_text(strip=True)
        description = BeautifulSoup(description, "html.parser").get_text()
        description = re.sub("<[^<]+?>", "", description)
        result = description.strip()
    else:
        result = html_snippet
    return result.replace("\n", " ")

class ScrapedDeal:
    category: str
    title: str
    summary: str
    url: str
    details: str
    features: str

    def __init__(self, entry: Dict[str, str]):
        self.title = entry["title"]
        self.summary = extract(entry["summary"])
        self.url = entry["links"][0]["href"]
        stuff = requests.get(self.url).content
        soup = BeautifulSoup(stuff, "html.parser")
        content_section = soup.find("div", class_="content-section")
        content = content_section.get_text() if content_section else self.summary
        content = content.replace("\nmore", "").replace("\n", " ")
        if "Features" in content:
            self.details, self.features = content.split("Features", 1)
        else:
            self.details = content
            self.features = ""
        self.truncate()

    def truncate(self):
        self.title = self.title[:100]
        self.details = self.details[:500]
        self.features = self.features[:500]

    def __repr__(self):
        return f"<{self.title}>"

    def describe(self):
        return f"Title: {self.title}\nDetails: {self.details.strip()}\nFeatures: {self.features.strip()}\nURL: {self.url}"

    @classmethod
    def fetch(cls, show_progress: bool = False) -> List['ScrapedDeal']:
        deals = []
        feed_iter = tqdm(feeds) if show_progress else feeds
        for feed_url in feed_iter:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                deals.append(cls(entry))
                time.sleep(0.05)
        return deals

class Deal(BaseModel):
    product_description: str = Field(
        description="Your clearly expressed summary of the used car in 3-4 sentences. Include make, model, year, and mileage if available. Avoid mentioning discounts; focus on the vehicle itself."
    )
    price: float = Field(
        description="The actual selling price of this vehicle. Respond with the final price."
    )
    url: str = Field(description="The URL of the listing.")

class DealSelection(BaseModel):
    deals: List[Deal] = Field(
        description="Your selection of the 5 vehicle deals that have the most detailed descriptions and clear pricing."
    )

class Opportunity(BaseModel):
    deal: Deal
    estimate: float
    discount: float