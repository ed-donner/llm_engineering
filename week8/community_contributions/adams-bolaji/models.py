"""
Real Estate Comps Agent - Data Models
=====================================
Pydantic models for properties, listings, and opportunities.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class SoldProperty(BaseModel):
    """A sold property used as a comparable (comp) for price estimation."""

    address: str
    city: str
    state: str
    zip_code: str
    bedrooms: int
    bathrooms: float
    sqft: int
    lot_sqft: Optional[int] = None
    year_built: Optional[int] = None
    sale_price: float
    sale_date: str
    description: str = ""

    def to_document(self) -> str:
        """Create a text representation for embedding and RAG retrieval."""
        parts = [
            f"{self.bedrooms} bed, {self.bathrooms} bath",
            f"{self.sqft} sqft",
            f"{self.city}, {self.state} {self.zip_code}",
            self.description or "",
        ]
        return " | ".join(p for p in parts if p).strip()

    def to_context_entry(self) -> str:
        """Format for inclusion in LLM context (includes price)."""
        return (
            f"Comp: {self.bedrooms} bed, {self.bathrooms} bath, {self.sqft} sqft "
            f"in {self.city}, {self.state}. Sold for ${self.sale_price:,.0f} on {self.sale_date}. "
            f"{self.description}"
        )


class Listing(BaseModel):
    """An active property listing (deal candidate)."""

    product_description: str = Field(
        description="Description of the property including beds, baths, sqft, location"
    )
    price: float = Field(description="Asking/list price of the property")
    url: str = Field(description="URL to the listing")

    # Optional structured fields for richer matching
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    city: Optional[str] = None
    state: Optional[str] = None


class ListingSelection(BaseModel):
    """Selection of listings from a scan."""

    listings: List[Listing] = Field(
        description="List of property listings with description, price, and URL"
    )


class PropertyOpportunity(BaseModel):
    """An opportunity: a listing priced below estimated fair value (comps-based)."""

    listing: Listing
    estimate: float  # Estimated fair value from comps
    discount: float  # estimate - listing.price (potential savings)
