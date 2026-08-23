import os
import sys
from typing import Optional, List
from openai import OpenAI

w8d5_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if w8d5_path not in sys.path:
    sys.path.insert(0, w8d5_path)

from agents.agent import Agent
from helpers.travel_deals import ScrapedTravelDeal, TravelDealSelection


class TravelScannerAgent(Agent):

    MODEL = "gpt-4o-mini"

    SYSTEM_PROMPT = """You identify and summarize the 5 most promising travel deals from a list.
    Focus on deals with destinations, deal types (flight/hotel/package), and detailed descriptions.
    If price is mentioned, extract it. If no specific price is given but there's a discount mentioned (e.g. "30% off"), estimate a reasonable price.
    If absolutely no pricing information exists, use a placeholder price of 500.
    Respond strictly in JSON with no explanation.
    
    {"deals": [
        {
            "destination": "City or Country name",
            "deal_type": "Flight, Hotel, or Package",
            "description": "4-5 sentences describing the travel deal, dates, what's included, and key highlights",
            "price": 499.99,
            "url": "the url as provided"
        },
        ...
    ]}"""
    
    USER_PROMPT_PREFIX = """Respond with the 5 most promising travel deals with destinations, types, and descriptions.
    Respond strictly in JSON. Provide detailed descriptions focusing on what travelers get.
    Extract the destination and deal type (Flight/Hotel/Package) from the title and description.
    For pricing: extract exact prices if available, estimate from percentage discounts, or use 500 as placeholder.
    
    Travel Deals:
    
    """

    USER_PROMPT_SUFFIX = "\n\nStrictly respond in JSON with exactly 5 deals."

    name = "Travel Scanner"
    color = Agent.CYAN

    def __init__(self):
        self.log("Travel Scanner is initializing")
        self.openai = OpenAI()
        self.log("Travel Scanner is ready")

    def fetch_deals(self, memory) -> List[ScrapedTravelDeal]:
        self.log("Travel Scanner fetching deals from RSS feeds")
        urls = [opp.deal.url for opp in memory]
        scraped = ScrapedTravelDeal.fetch()
        result = [scrape for scrape in scraped if scrape.url not in urls]
        self.log(f"Travel Scanner found {len(result)} new deals")
        return result

    def make_user_prompt(self, scraped) -> str:
        user_prompt = self.USER_PROMPT_PREFIX
        user_prompt += '\n\n'.join([scrape.describe() for scrape in scraped])
        user_prompt += self.USER_PROMPT_SUFFIX
        return user_prompt

    def scan(self, memory: List[str]=[]) -> Optional[TravelDealSelection]:
        scraped = self.fetch_deals(memory)
        if scraped:
            user_prompt = self.make_user_prompt(scraped)
            self.log("Travel Scanner calling OpenAI")
            result = self.openai.beta.chat.completions.parse(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
              ],
                response_format=TravelDealSelection
            )
            result = result.choices[0].message.parsed
            valid_deals = [deal for deal in result.deals if deal.price > 0]
            result.deals = valid_deals
            self.log(f"Travel Scanner received {len(result.deals)} valid deals")
            return result if result.deals else None
        return None

