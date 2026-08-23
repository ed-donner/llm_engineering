"""
All agents in one file. Injects submodules so deal_agent_framework imports work.
"""
import logging
import os
import re
import sys
import time
from types import ModuleType
from typing import Dict, List, Optional, Self

import feedparser
import modal
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

feeds = [
    "https://www.dealnews.com/c142/Electronics/?rss=1",
    "https://www.dealnews.com/c39/Computers/?rss=1",
    "https://www.dealnews.com/f1912/Smart-Home/?rss=1",
]


def _extract(html_snippet: str) -> str:
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


class Agent:
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BG_BLACK = "\033[40m"
    RESET = "\033[0m"
    name: str = ""
    color: str = "\033[37m"

    def log(self, message):
        color_code = self.BG_BLACK + self.color
        logging.info(color_code + f"[{self.name}] {message}" + self.RESET)


class ScrapedDeal:
    def __init__(self, entry: Dict[str, str]):
        self.title = entry["title"]
        self.summary = _extract(entry["summary"])
        self.url = entry["links"][0]["href"]
        stuff = requests.get(self.url).content
        soup = BeautifulSoup(stuff, "html.parser")
        content = soup.find("div", class_="content-section")
        content = content.get_text() if content else ""
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
    def fetch(cls, show_progress: bool = False) -> List[Self]:
        deals = []
        feed_iter = tqdm(feeds) if show_progress else feeds
        for feed_url in feed_iter:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                deals.append(cls(entry))
                time.sleep(0.05)
        return deals


class Deal(BaseModel):
    product_description: str = Field(description="Summary of the product in 3-4 sentences.")
    price: float = Field(description="The actual price as advertised.")
    url: str = Field(description="The URL of the deal.")


class DealSelection(BaseModel):
    deals: List[Deal] = Field(description="5 deals with detailed description and clear price.")


class Opportunity(BaseModel):
    deal: Deal
    estimate: float
    discount: float


class SpecialistAgent(Agent):
    name = "Specialist Agent"
    color = Agent.RED

    def __init__(self):
        self.log("Specialist Agent is initializing - connecting to modal")
        Pricer = modal.Cls.from_name("pricer-service", "Pricer")
        self.pricer = Pricer()

    def price(self, description: str) -> float:
        self.log("Specialist Agent is calling remote fine-tuned model")
        result = self.pricer.price.remote(description)
        self.log(f"Specialist Agent completed - predicting ${result:.2f}")
        return result


class FrontierAgent(Agent):
    name = "Frontier Agent"
    color = Agent.BLUE
    MODEL = "gpt-4o-mini"

    def __init__(self, collection):
        self.log("Initializing Frontier Agent")
        self.client = OpenAI()
        self.collection = collection
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.log("Frontier Agent is ready")

    def make_context(self, similars: List[str], prices: List[float]) -> str:
        msg = "Here are similar items for context:\n\n"
        for s, p in zip(similars, prices):
            msg += f"Product: {s}\nPrice: ${p:.2f}\n\n"
        return msg

    def messages_for(self, description: str, similars: List[str], prices: List[float]) -> List[Dict[str, str]]:
        msg = f"Estimate the price of this product. Respond with the price only.\n\n{description}\n\n"
        msg += self.make_context(similars, prices)
        return [{"role": "user", "content": msg}]

    def find_similars(self, description: str):
        self.log("Frontier Agent is performing RAG search for 5 similar products")
        vector = self.model.encode([description])
        results = self.collection.query(query_embeddings=vector.astype(float).tolist(), n_results=5)
        documents = results["documents"][0][:]
        prices = [m["price"] for m in results["metadatas"][0][:]]
        self.log("Frontier Agent has found similar products")
        return documents, prices

    def get_price(self, s: str) -> float:
        s = s.replace("$", "").replace(",", "")
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(match.group()) if match else 0.0

    def price(self, description: str) -> float:
        documents, prices = self.find_similars(description)
        self.log(f"Frontier Agent calling {self.MODEL}")
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=self.messages_for(description, documents, prices),
            seed=42,
        )
        return self.get_price(response.choices[0].message.content)


class EnsembleAgent(Agent):
    name = "Ensemble Agent"
    color = Agent.YELLOW

    def __init__(self, collection):
        self.log("Initializing Ensemble Agent (specialist + frontier)")
        self.specialist = SpecialistAgent()
        self.frontier = FrontierAgent(collection)
        self.log("Ensemble Agent is ready")

    def price(self, description: str) -> float:
        self.log("Running Ensemble Agent")
        s = self.specialist.price(description)
        f = self.frontier.price(description)
        combined = 0.5 * s + 0.5 * f
        self.log(f"Ensemble Agent complete - returning ${combined:.2f}")
        return combined


class ScannerAgent(Agent):
    name = "Scanner Agent"
    color = Agent.CYAN
    MODEL = "gpt-4o-mini"
    SYSTEM_PROMPT = """Select the 5 most detailed deals with clear prices. Respond strictly in JSON.
For each: product_description (3-4 sentence summary), price (number), url. Focus on product details."""
    USER_PROMPT_PREFIX = "Select the 5 best deals with detailed descriptions and clear prices > 0.\n\nDeals:\n\n"
    USER_PROMPT_SUFFIX = "\n\nInclude exactly 5 deals."

    def __init__(self):
        self.log("Scanner Agent is initializing")
        self.openai = OpenAI()
        self.log("Scanner Agent is ready")

    def fetch_deals(self, memory) -> List[ScrapedDeal]:
        self.log("Scanner Agent fetching deals from RSS feed")
        urls = [opp.deal.url for opp in memory]
        scraped = ScrapedDeal.fetch()
        result = [s for s in scraped if s.url not in urls]
        self.log(f"Scanner Agent received {len(result)} new deals")
        return result

    def make_user_prompt(self, scraped) -> str:
        return self.USER_PROMPT_PREFIX + "\n\n".join([s.describe() for s in scraped]) + self.USER_PROMPT_SUFFIX

    def scan(self, memory: List = []) -> Optional[DealSelection]:
        scraped = self.fetch_deals(memory)
        if not scraped:
            return None
        self.log("Scanner Agent calling OpenAI")
        result = self.openai.chat.completions.parse(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": self.make_user_prompt(scraped)},
            ],
            response_format=DealSelection,
        )
        parsed = result.choices[0].message.parsed
        parsed.deals = [d for d in parsed.deals if d.price > 0]
        self.log(f"Scanner Agent received {len(parsed.deals)} deals")
        return parsed


class MessagingAgent(Agent):
    name = "Messaging Agent"
    color = Agent.WHITE

    def __init__(self):
        self.log("Messaging Agent is initializing")
        self.pushover_user = os.getenv("PUSHOVER_USER", "")
        self.pushover_token = os.getenv("PUSHOVER_TOKEN", "")

    def push(self, text):
        if not self.pushover_user or not self.pushover_token:
            self.log("Messaging Agent: PUSHOVER_USER/TOKEN not set, skipping push")
            return
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "user": self.pushover_user,
                "token": self.pushover_token,
                "message": text,
                "sound": "cashregister",
            },
        )

    def alert(self, opportunity: Opportunity):
        text = (
            f"Deal! Price=${opportunity.deal.price:.2f}, Estimate=${opportunity.estimate:.2f}, "
            f"Discount=${opportunity.discount:.2f} : {opportunity.deal.product_description[:80]}... "
            f"{opportunity.deal.url}"
        )
        self.push(text)
        self.log("Messaging Agent has completed")


class PlanningAgent(Agent):
    name = "Planning Agent"
    color = Agent.GREEN
    DEAL_THRESHOLD = 50

    def __init__(self, collection):
        self.log("Planning Agent is initializing")
        self.scanner = ScannerAgent()
        self.ensemble = EnsembleAgent(collection)
        self.messenger = MessagingAgent()
        self.log("Planning Agent is ready")

    def run(self, deal: Deal) -> Opportunity:
        self.log("Planning Agent is pricing a potential deal")
        estimate = self.ensemble.price(deal.product_description)
        discount = estimate - deal.price
        self.log(f"Planning Agent processed deal with discount ${discount:.2f}")
        return Opportunity(deal=deal, estimate=estimate, discount=discount)

    def plan(self, memory: List = []) -> Optional[Opportunity]:
        self.log("Planning Agent is kicking off a run")
        selection = self.scanner.scan(memory=memory)
        if not selection:
            return None
        opportunities = [self.run(d) for d in selection.deals[:5]]
        opportunities.sort(key=lambda o: o.discount, reverse=True)
        best = opportunities[0]
        self.log(f"Planning Agent best deal discount ${best.discount:.2f}")
        if best.discount > self.DEAL_THRESHOLD:
            self.messenger.alert(best)
        self.log("Planning Agent has completed a run")
        return best if best.discount > self.DEAL_THRESHOLD else None


# Inject submodules so deal_agent_framework's "from agents.planning_agent import PlanningAgent" works
def _inject_submodules():
    pkg = sys.modules[__name__]
    for name, mod_path in [
        ("agent", "agents.agent"),
        ("deals", "agents.deals"),
        ("specialist_agent", "agents.specialist_agent"),
        ("frontier_agent", "agents.frontier_agent"),
        ("ensemble_agent", "agents.ensemble_agent"),
        ("scanner_agent", "agents.scanner_agent"),
        ("messaging_agent", "agents.messaging_agent"),
        ("planning_agent", "agents.planning_agent"),
    ]:
        m = ModuleType(mod_path)
        if name == "agent":
            m.Agent = Agent
        elif name == "deals":
            m.ScrapedDeal = ScrapedDeal
            m.Deal = Deal
            m.DealSelection = DealSelection
            m.Opportunity = Opportunity
        elif name == "specialist_agent":
            m.SpecialistAgent = SpecialistAgent
        elif name == "frontier_agent":
            m.FrontierAgent = FrontierAgent
        elif name == "ensemble_agent":
            m.EnsembleAgent = EnsembleAgent
        elif name == "scanner_agent":
            m.ScannerAgent = ScannerAgent
        elif name == "messaging_agent":
            m.MessagingAgent = MessagingAgent
        elif name == "planning_agent":
            m.PlanningAgent = PlanningAgent
        sys.modules[mod_path] = m


_inject_submodules()
