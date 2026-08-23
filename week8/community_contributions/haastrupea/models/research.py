from pydantic import BaseModel
from typing import Optional


class SecuritiesEvent(BaseModel):
    ticker: str
    headline: str
    source_url: str
    published_at: Optional[str] = None
    summary: str = ""


class ResearchOpportunity(BaseModel):
    ticker: str
    recommendation: str
    confidence: float
    summary: str = ""
    url: str = ""
