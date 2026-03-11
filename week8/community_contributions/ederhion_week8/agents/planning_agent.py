from typing import Optional, List
from agents.agent import Agent
from agents.deals import Deal, Opportunity
from agents.scanner_agent import ScannerAgent
from agents.frontier_agent import FrontierAgent
from agents.messaging_agent import MessagingAgent

class PlanningAgent(Agent):
    name = "Planning Agent"
    color = Agent.GREEN
    DEAL_THRESHOLD = -50000  # Vehicles have larger margins, so we significantly increase the alert threshold

    def __init__(self, collection):
        self.log("Planning Agent is initializing")
        self.scanner = ScannerAgent()
        self.estimator = FrontierAgent(collection)
        self.messenger = MessagingAgent()
        self.log("Planning Agent is ready")

    def run(self, deal: Deal) -> Opportunity:
        self.log("Planning Agent is pricing up a potential vehicle deal")
        estimate = self.estimator.price(deal.product_description)
        discount = estimate - deal.price
        self.log(f"Planning Agent has processed a deal with discount ${discount:.2f}")
        return Opportunity(deal=deal, estimate=estimate, discount=discount)

    def plan(self, memory: List[str] = []) -> Optional[Opportunity]:
        self.log("Planning Agent is kicking off a run")
        selection = self.scanner.test_scan(memory=memory)
        if selection:
            opportunities = [self.run(deal) for deal in selection.deals[:5]]
            opportunities.sort(key=lambda opp: opp.discount, reverse=True)
            best = opportunities[0]
            self.log(f"Planning Agent has identified the best deal has discount ${best.discount:.2f}")
            if best.discount > self.DEAL_THRESHOLD:
                self.messenger.alert(best)
            self.log("Planning Agent has completed a run")
            return best if best.discount > self.DEAL_THRESHOLD else None
        return None