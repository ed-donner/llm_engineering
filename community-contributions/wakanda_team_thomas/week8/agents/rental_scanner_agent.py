from openai import OpenAI
from agents.agent import Agent
from agents.rental_deals import (
    ScrapedListing,
    RentalDeal,
    DealSelection,
    fetch_all_listings,
    scraped_to_deal,
)


class RentalScannerAgent(Agent):
    """Scans listings and uses GPT to select the best rental deals."""

    name = "Scanner"
    color = "cyan"

    SYSTEM_PROMPT = """You are a rental deal analyst. You will receive a list of rental listings
from New York, Lagos, and Nairobi. Select the 5 best deals — listings that appear
to offer the most value for money based on price, size, location, and features.

Only select listings with a clear monthly rent price greater than $0.
Provide brief reasoning for your selections."""

    def __init__(self):
        self.client = OpenAI()

    def scan(self, count_per_city: int = 10) -> list[RentalDeal]:
        self.log("Scanning rental listings across New York, Lagos, and Nairobi...")
        listings = fetch_all_listings(count_per_city=count_per_city)
        self.log(f"Found {len(listings)} listings. Asking GPT to select the best deals...")

        deals = self._select_best(listings)
        self.log(f"Selected {len(deals)} top deals.")
        return deals

    def _select_best(self, listings: list[ScrapedListing]) -> list[RentalDeal]:
        listings_text = "\n\n".join(
            f"Listing {i+1}:\n"
            f"  Title: {l.title}\n"
            f"  City: {l.city}\n"
            f"  Price: ${l.price:,.2f}/month\n"
            f"  Description: {l.description}\n"
            f"  URL: {l.url}"
            for i, l in enumerate(listings)
        )

        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"Here are the listings:\n\n{listings_text}"},
            ],
            response_format=DealSelection,
        )

        selection = response.choices[0].message.parsed
        self.log(f"Reasoning: {selection.reasoning}")
        return [deal for deal in selection.deals if deal.rent > 0]
