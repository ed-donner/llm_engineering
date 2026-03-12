"""
Scanner agent: produces a list of flight routes to price.
Can use a static list, the dataset's unique routes, or an LLM to parse user queries.
Reference: week8 agents/scanner_agent.py, week6 Africa flight data.
"""

import os
import json
from pathlib import Path
from typing import List, Optional

from openai import OpenAI

from .agent import Agent
from .flight_deals import FlightRoute


class RouteScannerAgent(Agent):
    """
    Produces flight route requests to be priced by the specialist.
    Uses either a routes file, the dataset, or an optional LLM to parse natural language.
    """

    name = "Route Scanner Agent"
    color = Agent.CYAN

    def __init__(self, routes_file: Optional[Path] = None, use_llm: bool = False):
        self.log("Route Scanner Agent is initializing")
        self.routes_file = routes_file or Path(__file__).parent.parent / "data" / "routes.json"
        self.use_llm = use_llm
        self._client: Optional[OpenAI] = None
        if use_llm:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self._client = OpenAI(api_key=api_key)
        self.log("Route Scanner Agent is ready")

    def get_routes_from_file(self) -> List[FlightRoute]:
        """Load routes from a JSON file (list of {origin_city, origin_country, destination_city, destination_country})."""
        if not self.routes_file.exists():
            self.log(f"Routes file not found: {self.routes_file}; returning empty list")
            return []
        with open(self.routes_file, "r") as f:
            data = json.load(f)
        routes = [FlightRoute(**item) for item in data]
        self.log(f"Loaded {len(routes)} routes from {self.routes_file}")
        return routes

    def get_routes_from_query(self, query: str) -> List[FlightRoute]:
        """Use LLM to parse natural language into a list of FlightRoute. Requires OPENAI_API_KEY."""
        if not self._client:
            self.log("LLM not configured; cannot parse query. Set OPENAI_API_KEY and use_llm=True.")
            return []

        system = (
            "You extract flight route requests from the user's message. "
            "Respond with a JSON array of objects, each with: origin_city, origin_country, destination_city, destination_country. "
            "Use proper country and city names (e.g. Nigeria, Kenya, Lagos, Nairobi). "
            "Respond only with the JSON array, no other text."
        )
        try:
            resp = self._client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": query},
                ],
            )
            content = resp.choices[0].message.content or "[]"
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            data = json.loads(content)
            routes = [FlightRoute(**item) for item in data]
            self.log(f"Parsed {len(routes)} routes from user query")
            return routes
        except Exception as e:
            self.log(f"LLM parse failed: {e}; returning empty list")
            return []

    def scan(self, memory_urls: Optional[List[str]] = None, user_query: Optional[str] = None) -> List[FlightRoute]:
        """
        Return routes to price. If user_query is given and use_llm, parse it; else use routes file.
        memory_urls is ignored here (used in product-deal flow); we could filter already-seen routes later.
        """
        if user_query and self.use_llm:
            return self.get_routes_from_query(user_query)
        return self.get_routes_from_file()
