from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from agents.agent import Agent


class Listing(BaseModel):
    """
    One offer for a product at one retailer
    """

    retailer: str = Field(description="The name of the store selling it, for example Walmart or Best Buy")
    price: float = Field(description="The current selling price in US dollars at this retailer")
    url: str = Field(description="The URL of the page this price came from. Never invent one.")


class PriceLookup(BaseModel):
    """
    What a product currently sells for, according to a web search
    """

    found: bool = Field(
        description="True only if you identified this exact product and found at least one real offer for it"
    )
    product_name: str = Field(description="The full name of the product you found, including its model number")
    listings: List[Listing] = Field(
        description="Every offer you found for this exact product, one entry per retailer. Leave empty if found is false."
    )


class VerifiedPrice(BaseModel):
    """
    The cheapest way to buy this product elsewhere, which is what a deal should be measured against
    """

    product_name: str
    price: float
    retailer: str
    url: str
    highest: float
    count: int


class VerifierAgent(Agent):
    name = "Verifier Agent"
    color = Agent.MAGENTA

    MODEL = "gpt-5.1"

    SYSTEM_PROMPT = """You look up what a product currently sells for, using web search.

Search several retailers, not just the first one you find, and report every offer you find as a separate listing with the retailer, the price and the URL it came from.

A listing only counts if all of these hold:
- it is the same product, matching on model number where there is one
- it is in the same condition as the product described, so do not offer a refurbished unit for a new product or the other way around
- it is sold by the retailer itself, not by a third party seller on a marketplace
- the price is what a shopper pays today, not the manufacturer's list price or MSRP, and not a limited time promotional or clearance price

Never invent a listing or a URL. Reporting fewer listings is fine, and reporting none is much better than reporting the price of a similar but different product. If the description is too vague to identify one specific product, or you cannot find that product for sale, set found to false and return no listings."""

    def __init__(self):
        self.log("Verifier Agent is initializing")
        self.client = OpenAI()
        self.log("Verifier Agent is ready")

    def lookup(self, description: str) -> Optional[VerifiedPrice]:
        """
        Search the web for what this product sells for elsewhere
        :param description: the product description scraped from the deal
        :return: the cheapest valid listing found, or None if the product could not be identified
        """
        self.log(f"Verifier Agent is searching the web using {self.MODEL}")
        response = self.client.responses.parse(
            model=self.MODEL,
            tools=[{"type": "web_search"}],
            input=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": description},
            ],
            text_format=PriceLookup,
        )
        result = response.output_parsed
        if not result or not result.found:
            self.log("Verifier Agent could not identify this product online")
            return None

        # The schema allows any number and any list, so drop anything that cannot be an offer
        listings = [listing for listing in result.listings if listing.price > 0 and listing.url]
        if not listings:
            self.log("Verifier Agent found no usable listings for this product")
            return None

        cheapest = listings[0]
        highest = listings[0].price
        for listing in listings:
            if listing.price < cheapest.price:
                cheapest = listing
            if listing.price > highest:
                highest = listing.price

        self.log(
            f"Verifier Agent found {len(listings)} listing(s) for {result.product_name}, "
            f"cheapest ${cheapest.price:.2f} at {cheapest.retailer}, highest ${highest:.2f}"
        )
        return VerifiedPrice(
            product_name=result.product_name,
            price=cheapest.price,
            retailer=cheapest.retailer,
            url=cheapest.url,
            highest=highest,
            count=len(listings),
        )
