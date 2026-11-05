from pydantic import BaseModel, Field
from typing import List, Dict, Self
from bs4 import BeautifulSoup
import hashlib
import logging
import re
import feedparser
from tqdm import tqdm
import requests
import time

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"}

# RSS feeds of deals: (name, url, currency)
feeds = [
    ("HotUKDeals", "https://www.hotukdeals.com/rss/tag/wine", "GBP"),
]

# Wine sites that show their current offer on the home page: (name, url, currency)
# To add a shop later (for example in Kenya or South Africa), add a line here
pages = [
    ("WTSO", "https://www.wtso.com/", "USD"),
    ("Last Bottle", "https://www.lastbottlewines.com/", "USD"),
]

FALLBACK_GBP_TO_USD = 1.32


def extract(html_snippet: str) -> str:
    """
    Use Beautiful Soup to clean up this HTML snippet and extract useful text
    """
    text = BeautifulSoup(html_snippet, "html.parser").get_text(" ")
    return " ".join(text.split())


def gbp_to_usd() -> float:
    """
    Today's exchange rate from a free service, or a fixed fallback if it can't be reached
    """
    try:
        rates = requests.get("https://open.er-api.com/v6/latest/GBP", timeout=15).json()["rates"]
        return float(rates["USD"])
    except Exception:
        logging.warning(f"Could not fetch the exchange rate, using {FALLBACK_GBP_TO_USD}")
        return FALLBACK_GBP_TO_USD


class ScrapedDeal:
    """
    A class to represent a possible wine deal, read from an RSS feed or a shop's home page
    """

    source: str
    title: str
    details: str
    url: str
    currency: str

    def __init__(self, source: str, title: str, details: str, url: str, currency: str):
        self.source = source
        self.title = title[:150]
        self.details = details[:1200]
        self.url = url
        self.currency = currency

    def __repr__(self):
        return f"<{self.source}: {self.title}>"

    def describe(self):
        """
        Return a longer string to describe this deal for use in calling a model
        """
        return (
            f"Source: {self.source}\nCurrency: {self.currency}\nTitle: {self.title}\n"
            f"Details: {self.details}\nURL: {self.url}"
        )

    @classmethod
    def from_rss_entry(cls, entry: Dict, source: str, currency: str) -> Self:
        return cls(
            source=source,
            title=entry["title"],
            details=extract(entry.get("summary", "")),
            url=entry["link"],
            currency=currency,
        )

    @classmethod
    def from_page(cls, source: str, url: str, currency: str) -> Self:
        """
        Read a shop's home page and keep the text around the first price, which is where the current offer is
        """
        html = requests.get(url, headers=HEADERS, timeout=30).text
        text = extract(html)
        first_price = text.find("$")
        start = max(0, first_price - 300)
        details = text[start : start + 1500]
        # The page address never changes, so add a fingerprint of the offer to tell one day's deal from the next
        fingerprint = hashlib.md5(details[:400].encode()).hexdigest()[:10]
        return cls(source=source, title=f"Current offer at {source}", details=details, url=f"{url}#{fingerprint}", currency=currency)

    @classmethod
    def fetch(cls, show_progress: bool = False) -> List[Self]:
        """
        Retrieve all deals from the feeds and the shop pages.
        A source that fails is skipped, so one broken site doesn't stop the others
        """
        deals = []
        # The US shops come first: their prices are in the same market our models learned
        page_iter = tqdm(pages) if show_progress else pages
        for source, page_url, currency in page_iter:
            try:
                deals.append(cls.from_page(source, page_url, currency))
                time.sleep(0.5)
            except Exception as e:
                logging.warning(f"Skipping {source}: {e}")
        feed_iter = tqdm(feeds) if show_progress else feeds
        for source, feed_url, currency in feed_iter:
            try:
                feed = feedparser.parse(requests.get(feed_url, headers=HEADERS, timeout=30).content)
                for entry in feed.entries[:10]:
                    deals.append(cls.from_rss_entry(entry, source, currency))
            except Exception as e:
                logging.warning(f"Skipping {source}: {e}")
        return deals


class Deal(BaseModel):
    """
    A class to Represent a Deal with a summary description
    """

    product_description: str = Field(
        description="Your summary of the wine itself in 3-4 sentences: producer, wine name, grape, region and country, vintage, any critic score, and what it tastes like if the text says. Do not mention discounts, shipping or the terms of the deal."
    )
    price: float = Field(
        description="The price of ONE 750ml bottle in this deal, in the deal's own currency. If the deal is for a case or several bottles, divide by the number of bottles. If a deal has several prices, use the lowest price that a buyer of one bottle or a few bottles actually pays."
    )
    currency: str = Field(description="The currency of the price: USD or GBP")
    url: str = Field(description="The URL of the deal, exactly as provided in the input")


class DealSelection(BaseModel):
    """
    A class to Represent a list of Deals
    """

    deals: List[Deal] = Field(
        description="Your selection of up to 5 wine deals with the clearest description and the clearest price per bottle"
    )


class Opportunity(BaseModel):
    """
    A class to represent a possible opportunity: a Deal where we estimate
    it should cost more than it's being offered
    """

    deal: Deal
    estimate: float
    discount: float
