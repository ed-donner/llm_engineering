"""Planning agent: orchestrates scan -> score -> filter -> alert."""
from typing import List, Optional

from agents.agent import Agent
from agents.scanner_agent import ScannerAgent
from agents.ensemble_agent import EnsembleAgent
from agents.messaging_agent import MessagingAgent
from config import FIT_THRESHOLD, MAX_OPPORTUNITIES_PER_RUN
from publisher_models import PublisherOpportunity, ScoredOpportunity


class PlanningAgent(Agent):
    name = "Planning Agent"
    color = Agent.GREEN

    def __init__(self) -> None:
        self.log("Planning Agent is initializing")
        self.scanner = ScannerAgent()
        self.ensemble = EnsembleAgent()
        self.messenger = MessagingAgent()
        self.log("Planning Agent is ready")

    def plan(self, memory: List[ScoredOpportunity]) -> Optional[ScoredOpportunity]:
        """
        Scan for new opportunities, score them, and optionally alert on the best one if above threshold.
        Returns the best ScoredOpportunity if one was above threshold, else None.
        """
        self.log("Planning Agent is starting a run")
        new_opps = self.scanner.scan(memory=memory)
        if not new_opps:
            self.log("No new opportunities to score")
            return None
        to_score = new_opps[:MAX_OPPORTUNITIES_PER_RUN]
        scored: List[ScoredOpportunity] = []
        for opp in to_score:
            s = self.ensemble.score(opp)
            scored.append(s)
        scored.sort(key=lambda x: x.fit_score, reverse=True)
        best = scored[0]
        self.log(f"Best opportunity: {best.opportunity.name} (fit={best.fit_score:.1f})")
        if best.fit_score >= FIT_THRESHOLD:
            self.messenger.alert(best)
            self.log("Planning Agent completed; best opportunity alerted")
            return best
        self.log(f"Best fit below threshold {FIT_THRESHOLD}; no alert sent")
        return best
