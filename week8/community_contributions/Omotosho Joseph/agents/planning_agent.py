from typing import Optional, List
from agents.agent import Agent
from agents.job_listings import JobListing, JobSelection, JobOpportunity
from agents.scanner_agent import ScannerAgent
from agents.ensemble_agent import EnsembleAgent
from agents.messaging_agent import MessagingAgent


class PlanningAgent(Agent):
    """
    Simple orchestrator: scan for jobs, estimate market salaries,
    identify the best opportunity, and notify the user.
    """

    name = "Planning Agent"
    color = Agent.GREEN
    PREMIUM_THRESHOLD = 10_000

    def __init__(self, collection):
        self.log("Planning Agent is initializing")
        self.scanner = ScannerAgent()
        self.ensemble = EnsembleAgent(collection)
        self.messenger = MessagingAgent()
        self.log("Planning Agent is ready")

    def run(self, listing: JobListing) -> JobOpportunity:
        self.log("Planning Agent is estimating market salary for a listing")
        estimate = self.ensemble.estimate(listing.description)
        premium = listing.salary - estimate
        self.log(f"Planning Agent processed listing - premium ${premium:,.0f}")
        return JobOpportunity(listing=listing, estimate=estimate, premium=premium)

    def plan(self, memory: List[str] = []) -> Optional[JobOpportunity]:
        """
        Full workflow:
        1. ScannerAgent finds job listings from RSS feeds
        2. EnsembleAgent estimates market salary for each
        3. MessagingAgent notifies user of best above-market opportunity
        """
        self.log("Planning Agent is kicking off a run")
        selection = self.scanner.scan(memory=memory)
        if selection:
            opportunities = [self.run(listing) for listing in selection.listings[:5]]
            opportunities.sort(key=lambda opp: opp.premium, reverse=True)
            best = opportunities[0]
            self.log(
                f"Planning Agent identified best opportunity with premium ${best.premium:,.0f}"
            )
            if best.premium > self.PREMIUM_THRESHOLD:
                self.messenger.alert(best)
            self.log("Planning Agent has completed a run")
            return best if best.premium > self.PREMIUM_THRESHOLD else None
        return None
