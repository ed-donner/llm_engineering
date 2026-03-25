from typing import Optional, List
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from agents.agent import Agent
from agents.deals import Deal, Opportunity
from agents.scanner_agent import ScannerAgent
from agents.ensemble_agent import EnsembleAgent
from agents.messaging_agent import MessagingAgent
from openai import OpenAI
import json


class Verdict(BaseModel):
    """
    A structured verdict on whether a deal is worth buying,
    produced by comparing it against competing products in the vector store.
    """

    decision: str = Field(description="One of: buy, pass, wait")
    reasoning: str = Field(
        description="2-3 sentence explanation of the decision"
    )
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")
    competing_product_summary: str = Field(
        description="Brief summary of how this deal compares to similar products in the database"
    )


class NegotiationAgent(Agent):
    """
    An autonomous agent that extends the AutonomousPlanningAgent pattern with
    two additional tools: RAG-based competitor lookup and structured verdict
    generation. The LLM orchestrates a 5-tool workflow to scan deals, estimate
    values, find competitors, compare, and conditionally notify the user.
    """

    name = "Negotiation Agent"
    color = Agent.CYAN
    MODEL = "gpt-5.1"

    def __init__(self, collection):
        self.log("Negotiation Agent is initializing")
        self.scanner = ScannerAgent()
        self.ensemble = EnsembleAgent(collection)
        self.messenger = MessagingAgent()
        self.collection = collection
        self.encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.openai = OpenAI()
        self.memory = None
        self.opportunity = None
        self.verdict = None
        self.log("Negotiation Agent is ready")

    # ── Tool implementations ─────────────────────────────────────────────

    def scan_the_internet_for_bargains(self) -> str:
        self.log("Negotiation Agent is calling scanner")
        results = self.scanner.scan(memory=self.memory)
        return results.model_dump_json() if results else "No deals found"

    def estimate_true_value(self, description: str) -> str:
        self.log("Negotiation Agent is estimating value via Ensemble Agent")
        estimate = self.ensemble.price(description)
        return f"The estimated true value of {description} is ${estimate:.2f}"

    def find_competing_products(self, description: str) -> str:
        self.log("Negotiation Agent is searching ChromaDB for competing products")
        vector = self.encoder.encode([description])
        results = self.collection.query(
            query_embeddings=vector.astype(float).tolist(), n_results=5
        )
        documents = results["documents"][0][:]
        prices = [m["price"] for m in results["metadatas"][0][:]]
        competitors = [
            {"description": doc, "price": price}
            for doc, price in zip(documents, prices)
        ]
        self.log(f"Negotiation Agent found {len(competitors)} competing products")
        return json.dumps(competitors)

    def compare_and_decide(
        self,
        description: str,
        deal_price: float,
        estimated_value: float,
        competing_products_json: str,
    ) -> str:
        self.log("Negotiation Agent is generating a verdict via Structured Outputs")
        user_prompt = (
            f"You are evaluating whether to recommend a deal to a user.\n\n"
            f"Deal description: {description}\n"
            f"Deal price: ${deal_price:.2f}\n"
            f"Estimated true value: ${estimated_value:.2f}\n\n"
            f"Here are similar products from our database for comparison:\n"
            f"{competing_products_json}\n\n"
            f"Based on the discount (estimated value minus deal price), the competing product prices, "
            f"and the quality of the deal, decide: buy, pass, or wait.\n"
            f"- 'buy' means the deal is compelling and the user should act now.\n"
            f"- 'pass' means the deal is not worth it.\n"
            f"- 'wait' means it might get better or needs more research."
        )
        response = self.openai.chat.completions.parse(
            model=self.MODEL,
            messages=[{"role": "user", "content": user_prompt}],
            response_format=Verdict,
        )
        verdict = response.choices[0].message.parsed
        self.verdict = verdict
        self.log(
            f"Negotiation Agent verdict: {verdict.decision} (confidence: {verdict.confidence:.2f})"
        )
        return verdict.model_dump_json()

    def notify_user_of_deal(
        self, description: str, deal_price: float, estimated_true_value: float, url: str
    ) -> str:
        if self.opportunity:
            self.log("Negotiation Agent is trying to notify a 2nd time; ignoring")
        else:
            self.log("Negotiation Agent is notifying user of recommended deal")
            self.messenger.notify(description, deal_price, estimated_true_value, url)
            deal = Deal(product_description=description, price=deal_price, url=url)
            discount = estimated_true_value - deal_price
            self.opportunity = Opportunity(
                deal=deal, estimate=estimated_true_value, discount=discount
            )
        return "Notification sent ok"

    # ── Tool JSON schemas ────────────────────────────────────────────────

    scan_function = {
        "name": "scan_the_internet_for_bargains",
        "description": "Returns top bargains scraped from the internet along with the price each item is being offered for",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    }

    estimate_function = {
        "name": "estimate_true_value",
        "description": "Given the description of an item, estimate how much it is actually worth",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "The description of the item to be estimated",
                },
            },
            "required": ["description"],
            "additionalProperties": False,
        },
    }

    find_competing_function = {
        "name": "find_competing_products",
        "description": "Search the product database (vector store) for products similar to the given description, returning their descriptions and prices",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "The description of the product to find competitors for",
                },
            },
            "required": ["description"],
            "additionalProperties": False,
        },
    }

    compare_function = {
        "name": "compare_and_decide",
        "description": "Compare a deal against competing products and produce a buy/pass/wait verdict with reasoning. Call this after estimating value and finding competitors.",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "The description of the deal product",
                },
                "deal_price": {
                    "type": "number",
                    "description": "The price the deal is being offered at",
                },
                "estimated_value": {
                    "type": "number",
                    "description": "The estimated true value of the product",
                },
                "competing_products_json": {
                    "type": "string",
                    "description": "JSON string of competing products from the database, each with description and price",
                },
            },
            "required": [
                "description",
                "deal_price",
                "estimated_value",
                "competing_products_json",
            ],
            "additionalProperties": False,
        },
    }

    notify_function = {
        "name": "notify_user_of_deal",
        "description": "Send the user a push notification about a deal; only call this if the verdict decision is 'buy'",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "The description of the item",
                },
                "deal_price": {
                    "type": "number",
                    "description": "The price offered by the deal",
                },
                "estimated_true_value": {
                    "type": "number",
                    "description": "The estimated actual value of the product",
                },
                "url": {
                    "type": "string",
                    "description": "The URL of the deal",
                },
            },
            "required": ["description", "deal_price", "estimated_true_value", "url"],
            "additionalProperties": False,
        },
    }

    def get_tools(self):
        return [
            {"type": "function", "function": self.scan_function},
            {"type": "function", "function": self.estimate_function},
            {"type": "function", "function": self.find_competing_function},
            {"type": "function", "function": self.compare_function},
            {"type": "function", "function": self.notify_function},
        ]

    def handle_tool_call(self, message):
        mapping = {
            "scan_the_internet_for_bargains": self.scan_the_internet_for_bargains,
            "estimate_true_value": self.estimate_true_value,
            "find_competing_products": self.find_competing_products,
            "compare_and_decide": self.compare_and_decide,
            "notify_user_of_deal": self.notify_user_of_deal,
        }
        results = []
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            tool = mapping.get(tool_name)
            result = tool(**arguments) if tool else ""
            results.append({"role": "tool", "content": result, "tool_call_id": tool_call.id})
        return results

    # ── Prompts ──────────────────────────────────────────────────────────

    system_message = (
        "You are a deal negotiation specialist. You use your tools to find deals, "
        "evaluate them against market data, and only recommend purchases that are "
        "truly compelling. You are methodical: scan, estimate, research competitors, "
        "compare, and only then decide whether to notify the user."
    )

    user_message = """
    Follow these steps using your tools:
    1. Scan the internet for bargain deals.
    2. For each deal, estimate its true value.
    3. Pick the deal with the largest discount (estimated value minus deal price).
    4. For that best deal, find competing products in the database.
    5. Compare the deal against the competitors to produce a verdict (buy, pass, or wait).
    6. ONLY if the verdict is 'buy', notify the user of the deal.
    7. Reply with a brief summary of the verdict and your reasoning.
    """

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

    # ── Main loop ────────────────────────────────────────────────────────

    def negotiate(self, memory: List = []) -> tuple[Optional[Verdict], Optional[Opportunity]]:
        """
        Run the full negotiation workflow autonomously.
        The LLM decides tool ordering and whether to notify.
        :param memory: list of Opportunity objects already surfaced
        :return: (verdict, opportunity) -- opportunity is None if verdict was not 'buy'
        """
        self.log("Negotiation Agent is kicking off a run")
        self.memory = memory
        self.opportunity = None
        self.verdict = None
        messages = self.messages[:]
        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model=self.MODEL, messages=messages, tools=self.get_tools()
            )
            if response.choices[0].finish_reason == "tool_calls":
                message = response.choices[0].message
                results = self.handle_tool_call(message)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        reply = response.choices[0].message.content
        self.log(f"Negotiation Agent completed with: {reply}")
        return self.verdict, self.opportunity
