"""
Specialist agent: returns flight price for a route using Africa flight data.
Uses Karosi/africa-flight-prices (week6 reference). No Modal dependency.
Reference: week8 agents/specialist_agent.py, week6 adeyemi-kayode dataset.
"""

import os
from pathlib import Path
from typing import Optional

from .agent import Agent
from .flight_deals import FlightRoute, FlightQuote


class FlightPricerAgent(Agent):
    """
    Looks up or estimates flight price for a route. Uses Hugging Face dataset
    Karosi/africa-flight-prices; optional OpenAI for unknown routes.
    """

    name = "Flight Pricer Agent"
    color = Agent.RED

    def __init__(self, dataset_path: Optional[Path] = None):
        self.log("Flight Pricer Agent is initializing")
        self._dataset = None
        self._dataset_path = dataset_path
        self._load_dataset()
        self.log("Flight Pricer Agent is ready")

    def _load_dataset(self) -> None:
        try:
            from datasets import load_dataset
            ds = load_dataset("Karosi/africa-flight-prices", split="train")
            self._dataset = ds.to_pandas()
            self.log(f"Loaded {len(self._dataset)} flight prices from Hugging Face")
        except Exception as e:
            self.log(f"Could not load HF dataset: {e}. Using local CSV if present.")
            self._dataset = None
            local = self._dataset_path or Path(__file__).parent.parent / "data" / "flight_prices_africa.csv"
            if local.exists():
                import pandas as pd
                self._dataset = pd.read_csv(local)
                self._dataset["price_usd"] = self._dataset["price_usd"].astype(float)
                self.log(f"Loaded {len(self._dataset)} rows from {local}")

    def _lookup(self, route: FlightRoute) -> Optional[float]:
        """Exact match on origin/destination. Returns price_usd or None."""
        if self._dataset is None:
            return None
        df = self._dataset
        mask = (
            (df["origin_city"] == route.origin_city)
            & (df["origin_country"] == route.origin_country)
            & (df["destination_city"] == route.destination_city)
            & (df["destination_country"] == route.destination_country)
        )
        hit = df.loc[mask]
        if hit.empty:
            return None
        return float(hit["price_usd"].iloc[0])

    def price(self, route: FlightRoute) -> FlightQuote:
        """
        Return a FlightQuote for the route. Uses dataset lookup; if not found,
        returns a placeholder quote with price 0 and source 'unknown'.
        """
        self.log(f"Pricing route: {route.describe()}")
        p = self._lookup(route)
        if p is not None:
            self.log(f"Found price ${p:.2f}")
            return FlightQuote(route=route, price_usd=p, source="dataset")
        self.log("Route not in dataset; returning placeholder $0")
        return FlightQuote(route=route, price_usd=0.0, source="unknown")
