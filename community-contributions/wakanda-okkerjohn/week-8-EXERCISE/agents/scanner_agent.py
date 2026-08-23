"""Scanner agent: loads curated opportunities and returns those not yet in memory."""
import json
import logging
from pathlib import Path
from typing import List, Optional

from agents.agent import Agent
from publisher_models import PublisherOpportunity, ScoredOpportunity

# Path to curated opportunities JSON (next to project root)
DATA_PATH = Path(__file__).resolve().parent.parent / "opportunities_data.json"


class ScannerAgent(Agent):
    name = "Scanner Agent"
    color = Agent.CYAN

    def __init__(self) -> None:
        self.log("Scanner Agent is initializing")
        self._opportunities: Optional[List[PublisherOpportunity]] = None
        self.log("Scanner Agent is ready")

    def _load_opportunities(self) -> List[PublisherOpportunity]:
        if self._opportunities is not None:
            return self._opportunities
        if not DATA_PATH.exists():
            self.log(f"Opportunities file not found: {DATA_PATH}")
            return []
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._opportunities = [PublisherOpportunity(**item) for item in data]
        self.log(f"Loaded {len(self._opportunities)} opportunities from {DATA_PATH.name}")
        return self._opportunities

    def scan(
        self,
        memory: List[ScoredOpportunity],
    ) -> List[PublisherOpportunity]:
        """
        Return opportunities that are not already in memory (by URL).
        Memory is the list of opportunities we've already surfaced.
        """
        self.log("Scanner Agent is scanning for new opportunities")
        all_opps = self._load_opportunities()
        seen_urls = {s.opportunity.url for s in memory}
        new_opps = [o for o in all_opps if o.url not in seen_urls]
        self.log(f"Scanner Agent found {len(new_opps)} opportunities not in memory")
        return new_opps
