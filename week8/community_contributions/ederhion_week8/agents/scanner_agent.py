from typing import Optional, List
from openai import OpenAI
from agents.deals import ScrapedDeal, DealSelection
from agents.agent import Agent

class ScannerAgent(Agent):
    MODEL = "gpt-4o-mini"

    SYSTEM_PROMPT = """You identify and summarize the 5 most detailed used car deals from a list.
    Respond strictly in JSON (JavaScript Object Notation) format with no explanation. Provide the price as a number derived from the description.
    Most important is that you respond with the 5 cars that have the most detailed product descriptions (make, model, year, mileage) and a clear price.
    """

    USER_PROMPT_PREFIX = """Respond with the most promising 5 vehicle deals from this list, selecting those which have detailed descriptions and a price greater than 0.
    Rephrase the description to be a summary of the vehicle itself.
    
    Deals:
    
    """

    USER_PROMPT_SUFFIX = "\n\nInclude exactly 5 deals, no more."

    name = "Scanner Agent"
    color = Agent.CYAN

    def __init__(self):
        self.log("Scanner Agent is initializing")
        self.openai = OpenAI()
        self.log("Scanner Agent is ready")

    def fetch_deals(self, memory) -> List[ScrapedDeal]:
        self.log("Scanner Agent is about to fetch deals from the automotive RSS feed")
        urls = [opp.deal.url for opp in memory]
        scraped = ScrapedDeal.fetch()
        result = [scrape for scrape in scraped if scrape.url not in urls]
        self.log(f"Scanner Agent received {len(result)} deals not already scraped")
        return result

    def make_user_prompt(self, scraped) -> str:
        user_prompt = self.USER_PROMPT_PREFIX
        user_prompt += "\n\n".join([scrape.describe() for scraped in scraped])
        user_prompt += self.USER_PROMPT_SUFFIX
        return user_prompt

    def scan(self, memory: List[str] = []) -> Optional[DealSelection]:
        scraped = self.fetch_deals(memory)
        if scraped:
            user_prompt = self.make_user_prompt(scraped)
            self.log("Scanner Agent is calling OpenAI using Structured Outputs")
            result = self.openai.chat.completions.parse(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=DealSelection,
                reasoning_effort="none",
            )
            parsed_result = result.choices[0].message.parsed
            parsed_result.deals = [deal for deal in parsed_result.deals if deal.price > 0]
            self.log(f"Scanner Agent received {len(parsed_result.deals)} selected deals with price>0")
            return parsed_result
        return None

    def test_scan(self, memory: List[str] = []) -> Optional[DealSelection]:
        results = {
            "deals": [
                {
                    "product_description": "2018 Honda Accord EX-L with 45,000 miles. Features a 1.5L turbocharged engine, leather seats, and advanced safety features. Excellent condition.",
                    "price": 21000,
                    "url": "https://www.dealnews.com/fake-honda-accord"
                },
                {
                    "product_description": "2020 Toyota Camry SE with 30,000 miles. Includes sport suspension, 18-inch alloy wheels, and a 7-inch touchscreen infotainment system.",
                    "price": 23500,
                    "url": "https://www.dealnews.com/fake-toyota-camry"
                }
            ]
        }
        return DealSelection(**results)