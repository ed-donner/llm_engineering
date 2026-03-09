"""
Data models for Africa flight price deals.
Aligns with week6 adeyemi-kayode / Karosi/africa-flight-prices schema.
Reference: week8 agents/deals.py
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class FlightRoute(BaseModel):
    """A route request: origin and destination city/country."""

    origin_city: str = Field(description="Origin city, e.g. Lagos")
    origin_country: str = Field(description="Origin country, e.g. Nigeria")
    destination_city: str = Field(description="Destination city, e.g. Nairobi")
    destination_country: str = Field(description="Destination country, e.g. Kenya")

    def describe(self) -> str:
        return (
            f"{self.origin_city}, {self.origin_country} → "
            f"{self.destination_city}, {self.destination_country}"
        )


class FlightQuote(BaseModel):
    """A flight route with a price (from dataset or specialist)."""

    route: FlightRoute
    price_usd: float = Field(description="Price in USD")
    source: str = Field(default="dataset", description="e.g. dataset, specialist, llm")


class FlightOpportunity(BaseModel):
    """A surfaced opportunity: best quote(s) or a deal recommendation."""

    quote: FlightQuote
    rank: int = Field(default=1, description="1 = best price in the batch")
    message: Optional[str] = None
