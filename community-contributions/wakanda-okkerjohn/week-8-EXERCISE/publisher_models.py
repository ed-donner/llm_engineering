"""Pydantic models for publisher/funding opportunities."""
from pydantic import BaseModel, Field
from typing import Optional


class PublisherOpportunity(BaseModel):
    """A publisher or funding opportunity for indie devs."""

    name: str = Field(description="Name of the publisher, fund, or program")
    description: str = Field(description="Short description: what they offer, who can apply")
    deadline: str = Field(description="Deadline or 'Ongoing' if rolling")
    url: str = Field(description="Link to submission page or more info")
    source: str = Field(default="curated", description="e.g. curated, rss, scraped")
    eligibility_summary: Optional[str] = Field(
        default=None,
        description="Optional one-line eligibility (genre, team size, platform)",
    )


class ScoredOpportunity(BaseModel):
    """An opportunity with a fit score (0-100)."""

    opportunity: PublisherOpportunity
    fit_score: float = Field(ge=0, le=100, description="How well it matches indie-friendly criteria")
