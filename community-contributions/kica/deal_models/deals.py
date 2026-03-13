"""
Deal models for the Best Value Real Estate pipeline.
Copied from week8/agents/deals.py for self-contained use in the kica folder.
"""

from pydantic import BaseModel, Field
from typing import List


class Deal(BaseModel):
    """A Deal or listing with description, price, and URL."""

    product_description: str = Field(
        description="Summary of the product or listing in 3-4 sentences."
    )
    price: float = Field(description="The price (list price or deal price).")
    url: str = Field(description="The URL of the deal or listing.")


class DealSelection(BaseModel):
    """A list of Deals."""

    deals: List[Deal] = Field(description="List of deals or listings.")


class Opportunity(BaseModel):
    """A Deal plus its estimated value and discount/gap."""

    deal: Deal
    estimate: float
    discount: float
