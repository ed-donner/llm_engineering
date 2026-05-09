import re
from typing import List, Dict
from openai import OpenAI
from .base_agent import Agent


class LLMPriceAgent(Agent):
    """
    Direct LLM-based Price Estimation Agent.
    Uses GPT's world knowledge to estimate product prices.
    """

    name = "LLM Price Agent"
    color = Agent.GREEN
    MODEL = "gpt-4o-mini"

    def __init__(self, currency: str = "₦", market: str = "Nigerian"):
        """
        Initialize the LLM Price Agent.
        
        Args:
            currency: Currency symbol for pricing
            market: Target market for price estimation
        """
        self.log("Initializing LLM Price Agent")
        self.client = OpenAI()
        self.currency = currency
        self.market = market
        self.log("LLM Price Agent ready")

    def build_messages(self, description: str) -> List[Dict[str, str]]:
        """Build messages for the LLM API call."""
        system_prompt = f"""You are an expert {self.market} e-commerce price analyst.
        You have extensive knowledge of product pricing on platforms like Jumia, Konga, and local markets.
        Consider factors like:
        - Import duties and shipping costs to Nigeria
        - Local market demand and competition
        - Brand perception in {self.market} market
        - Exchange rates and inflation
        
        Provide accurate price estimates in {self.currency}.
        Respond with ONLY the numeric price, no explanation or currency symbol."""

        user_prompt = f"""Estimate the fair market price for this product in the {self.market} market:

{description}

Respond with only the numeric price."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    def extract_price(self, response: str) -> float:
        """Extract numeric price from response."""
        cleaned = response.replace(self.currency, "").replace(",", "").replace("₦", "").replace("$", "")
        match = re.search(r"[-+]?\d*\.?\d+", cleaned)
        return float(match.group()) if match else 0.0

    def price(self, description: str) -> float:
        """
        Estimate product price using LLM knowledge.
        
        Args:
            description: Product description
            
        Returns:
            Estimated price as float
        """
        self.log(f"Estimating price using {self.MODEL}")
        messages = self.build_messages(description)
        
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=messages,
            temperature=0.2,
            seed=42
        )
        
        result = self.extract_price(response.choices[0].message.content)
        self.log(f"LLM Agent estimate: {self.currency}{result:,.2f}")
        return result


class GroqPriceAgent(Agent):
    """
    Fast LLM-based Price Estimation using Groq.
    Optimized for speed with Llama models.
    """

    name = "Groq Price Agent"
    color = Agent.CYAN
    MODEL = "llama-3.1-70b-versatile"

    def __init__(self, currency: str = "₦", market: str = "Nigerian"):
        self.log("Initializing Groq Price Agent")
        from groq import Groq
        self.client = Groq()
        self.currency = currency
        self.market = market
        self.log("Groq Price Agent ready")

    def build_messages(self, description: str) -> List[Dict[str, str]]:
        system_prompt = f"""You are a {self.market} market price expert.
        Estimate product prices accurately for the {self.market} e-commerce market.
        Consider local market conditions, import costs, and demand.
        Respond with ONLY the numeric price, no text."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Price estimate for: {description}"}
        ]

    def extract_price(self, response: str) -> float:
        cleaned = response.replace(self.currency, "").replace(",", "").replace("₦", "")
        match = re.search(r"[-+]?\d*\.?\d+", cleaned)
        return float(match.group()) if match else 0.0

    def price(self, description: str) -> float:
        self.log(f"Fast estimation using {self.MODEL}")
        messages = self.build_messages(description)
        
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=messages,
            temperature=0.1
        )
        
        result = self.extract_price(response.choices[0].message.content)
        self.log(f"Groq Agent estimate: {self.currency}{result:,.2f}")
        return result
