from typing import Optional, List
from openai import OpenAI
from agents.deals import ScrapedDeal, DealSelection, gbp_to_usd
from agents.agent import Agent


class ScannerAgent(Agent):
    MODEL = "gpt-5-mini"

    SYSTEM_PROMPT = """You identify and summarize the best wine deals from a list, choosing those with the most detailed description of the wine and the clearest price per bottle.
    Respond strictly in JSON using the format you are given. Only include bottles of wine: leave out spirits, beer, glasses, gifts and accessories.
    Give the price of ONE 750ml bottle in the deal's own currency. For a case or a multipack, divide the total by the number of bottles; if you can't tell how many bottles there are, leave the deal out.
    Be careful with deals described as "$XXX off" or "reduced by $XXX" - that is not the price. Use the price the buyer actually pays. Only include deals when you are highly confident about the price.
    Always include the current offers from the US shops (WTSO and Last Bottle) when their price is clear: they are the most important deals.
    Use only facts stated in the text. Never add tasting notes, flavours or details that the text does not give.
    """

    USER_PROMPT_PREFIX = """Respond with the most promising wine deals from this list, up to 5, selecting those with the most detailed description of the wine and a clear price per bottle greater than 0.
    Rephrase each description to be a summary of the wine itself, not the terms of the deal.

    Deals:

    """

    USER_PROMPT_SUFFIX = "\n\nInclude at most 5 deals."

    name = "Scanner Agent"
    color = Agent.CYAN

    def __init__(self):
        """
        Set up this instance by initializing OpenAI
        """
        self.log("Scanner Agent is initializing")
        self.openai = OpenAI()
        self.log("Scanner Agent is ready")

    def fetch_deals(self, memory) -> List[ScrapedDeal]:
        """
        Look up deals in the feeds and shop pages
        Return any new deals that are not already in the memory provided
        """
        self.log("Scanner Agent is about to fetch deals from the feeds and shop pages")
        urls = [opp.deal.url for opp in memory]
        scraped = ScrapedDeal.fetch()
        result = [scrape for scrape in scraped if scrape.url not in urls]
        self.log(f"Scanner Agent received {len(result)} deals not already scraped")
        return result

    def make_user_prompt(self, scraped) -> str:
        """
        Create a user prompt for OpenAI based on the scraped deals provided
        """
        user_prompt = self.USER_PROMPT_PREFIX
        user_prompt += "\n\n".join([scrape.describe() for scrape in scraped])
        user_prompt += self.USER_PROMPT_SUFFIX
        return user_prompt

    def convert_to_usd(self, selection: DealSelection) -> DealSelection:
        """
        Our models learned US prices, so convert every price into dollars
        """
        rate = None
        for deal in selection.deals:
            if deal.currency.upper() == "GBP":
                rate = rate or gbp_to_usd()
                deal.price = round(deal.price * rate, 2)
                deal.currency = "USD"
        if rate:
            self.log(f"Scanner Agent converted pounds to dollars at {rate:.3f}")
        return selection

    def scan(self, memory: List = []) -> Optional[DealSelection]:
        """
        Call OpenAI to provide a high potential list of deals with good descriptions and prices
        Use Structured Outputs to ensure it conforms to our specifications
        :param memory: a list of Opportunities already raised
        :return: a selection of good deals, or None if there aren't any
        """
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
                reasoning_effort="minimal",
            )
            result = result.choices[0].message.parsed
            result.deals = [deal for deal in result.deals if deal.price > 0]
            result = self.convert_to_usd(result)
            self.log(f"Scanner Agent received {len(result.deals)} selected deals with price>0 from OpenAI")
            return result
        return None

    def test_scan(self, memory: List = []) -> Optional[DealSelection]:
        """
        Return a test DealSelection, to be used during testing without calling any website or model
        """
        results = {
            "deals": [
                {
                    "product_description": "Résonance Découverte Vineyard Pinot Noir 2017 from the Dundee Hills in Oregon's Willamette Valley, made by the Oregon project of Burgundy's Maison Louis Jadot. It scored 93 points from Wine Spectator. A library release of a hillside Pinot Noir.",
                    "price": 29.99,
                    "currency": "USD",
                    "url": "https://www.wtso.com/#test-resonance",
                },
                {
                    "product_description": "Decades 5 Cabernet Sauvignon 2023 from Napa Valley, California, made by winemaker Jean Hoefliger, known for Alpha Omega. It received 96 points. A full-bodied Napa Cabernet.",
                    "price": 49.0,
                    "currency": "USD",
                    "url": "https://www.lastbottlewines.com/#test-decades",
                },
                {
                    "product_description": "Brancott Estate Sauvignon Blanc from Marlborough, New Zealand. A crisp, aromatic white wine from one of the region's best-known producers.",
                    "price": 10.58,
                    "currency": "USD",
                    "url": "https://www.hotukdeals.com/deals/test-brancott",
                },
            ]
        }
        return DealSelection(**results)
