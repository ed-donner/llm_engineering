from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ScannedResource(BaseModel):
    title: str = Field(description="Human-readable title for the resource")
    url: str = Field(description="Canonical URL for the resource")
    source: str = Field(description="Source publisher, domain, or feed name")
    snippet: str = Field(description="A short summary snippet")
    published_at: str = Field(default_factory=utc_now_iso)

    def describe(self) -> str:
        return (
            f"Title: {self.title}\n"
            f"Source: {self.source}\n"
            f"Snippet: {self.snippet}\n"
            f"Published: {self.published_at}\n"
            f"URL: {self.url}"
        )


class ResourceSelection(BaseModel):
    resources: List[ScannedResource]


class ResourceOpportunity(BaseModel):
    resource: ScannedResource
    estimated_quality: float
    value_gap: float
    score_breakdown: dict = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
