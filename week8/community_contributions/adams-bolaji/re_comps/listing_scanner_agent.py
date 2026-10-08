"""
ListingScannerAgent - Discovers active property listings.
Uses sample/mock data for demo. Can be extended to scrape MLS, Zillow, or RSS feeds.
"""
import json
from pathlib import Path
from typing import List, Optional
from openai import OpenAI

from agents.agent import Agent

# Import models from parent adams-bolaji
import sys

adams_path = Path(__file__).resolve().parent.parent
if str(adams_path) not in sys.path:
    sys.path.insert(0, str(adams_path))

from models import Listing, ListingSelection


class ListingScannerAgent(Agent):
    """
    Scans for new property listings.
    Uses sample data for demo; in production, would integrate with MLS/Zillow APIs or RSS.
    """

    name = "Listing Scanner Agent"
    color = Agent.CYAN
    MODEL = "gpt-4o-mini"

    SYSTEM_PROMPT = """You identify and summarize property listings from a list.
    Select listings that have the most detailed description: beds, baths, sqft, location.
    Respond strictly in JSON with no explanation. Provide the asking price as a number.
    Only include listings where the price is clear and greater than 0.
    Focus on the property description, not marketing language."""

    USER_PROMPT_PREFIX = """Select the most promising property listings from this list.
    For each, provide a concise property description (beds, baths, sqft, location, key features)
    and the asking price. Include up to 5 listings with clear prices.

    Listings:
    """

    USER_PROMPT_SUFFIX = "\n\nInclude up to 5 listings with valid prices."

    def __init__(self):
        self.log("Listing Scanner Agent is initializing")
        self.openai = OpenAI()
        self._sample_listings_path = adams_path / "data" / "sample_listings.json"
        self.log("Listing Scanner Agent is ready")

    def _load_sample_listings(self) -> List[dict]:
        """Load sample listings from JSON."""
        if self._sample_listings_path.exists():
            with open(self._sample_listings_path) as f:
                return json.load(f)
        return self._get_default_listings()

    def _get_default_listings(self) -> List[dict]:
        """Fallback inline sample listings."""
        return [
            {
                "description": "3 bed, 2 bath, 1850 sqft single-family home in Oakwood. Updated kitchen, hardwood floors, fenced yard.",
                "asking_price": 285000,
                "url": "https://example.com/listings/oakwood-123",
            },
            {
                "description": "4 bed, 3 bath, 2200 sqft in Riverside Estates. New HVAC 2023, open floor plan, master suite.",
                "asking_price": 345000,
                "url": "https://example.com/listings/riverside-456",
            },
            {
                "description": "2 bed, 1.5 bath, 1200 sqft condo in Downtown. Granite counters, in-unit laundry, gym access.",
                "asking_price": 195000,
                "url": "https://example.com/listings/downtown-789",
            },
            {
                "description": "5 bed, 4 bath, 3200 sqft executive home in Lakeview. Pool, finished basement, 3-car garage.",
                "asking_price": 525000,
                "url": "https://example.com/listings/lakeview-101",
            },
            {
                "description": "3 bed, 2 bath, 1600 sqft ranch in suburban Meadowbrook. One-owner, large lot, move-in ready.",
                "asking_price": 265000,
                "url": "https://example.com/listings/meadowbrook-202",
            },
        ]

    def fetch_listings(self, memory: List) -> List[dict]:
        """Fetch listings, excluding any already in memory."""
        self.log("Listing Scanner Agent is fetching listings")
        all_listings = self._load_sample_listings()
        seen_urls = {opp.listing.url for opp in memory}
        new_listings = [l for l in all_listings if l.get("url", "") not in seen_urls]
        self.log(f"Listing Scanner Agent has {len(new_listings)} new listings")
        return new_listings

    def scan(self, memory: List = None) -> Optional[ListingSelection]:
        """
        Scan for listings and return a selection.
        Uses sample data; formats for LLM parsing if raw data needs refinement.
        """
        memory = memory or []
        listings_data = self.fetch_listings(memory)

        if not listings_data:
            self.log("Listing Scanner Agent: No new listings found")
            return None

        # Convert to ListingSelection format
        listings = [
            Listing(
                product_description=l["description"],
                price=float(l["asking_price"]),
                url=l.get("url", ""),
            )
            for l in listings_data[:5]
        ]
        selection = ListingSelection(listings=listings)
        self.log(f"Listing Scanner Agent returning {len(listings)} listings")
        return selection
