from typing import Optional, List
from agents.agent import Agent
from agents.deals import Deal, Opportunity
from agents.scanner_agent import ScannerAgent
from agents.ensemble_agent import EnsembleAgent
from agents.messaging_agent import MessagingAgent


class PlanningAgent(Agent):

    name = "Planning Agent"
    color = Agent.GREEN

    # Ed alerted when the discount was over $50, which suited products costing hundreds of dollars.
    # Most of our wines cost $10-$50, so we alert when the estimate is at least 30% above the price
    # and at least $10 more
    MIN_DISCOUNT = 10
    MIN_DISCOUNT_RATIO = 0.3

    def __init__(self, client, use_specialist: bool = True):
        """
        Create instances of the 3 Agents that this planner coordinates across
        :param client: an open QdrantClient, for the Frontier Agent's RAG search
        """
        self.log("Planning Agent is initializing")
        self.scanner = ScannerAgent()
        self.ensemble = EnsembleAgent(client, use_specialist=use_specialist)
        self.messenger = MessagingAgent()
        self.log("Planning Agent is ready")

    def is_worth_alerting(self, opportunity: Opportunity) -> bool:
        return (
            opportunity.discount >= self.MIN_DISCOUNT
            and opportunity.discount >= self.MIN_DISCOUNT_RATIO * opportunity.deal.price
        )

    def run(self, deal: Deal) -> Opportunity:
        """
        Run the workflow for a particular deal
        :param deal: the deal, summarized from a scrape
        :returns: an opportunity including the discount
        """
        self.log("Planning Agent is pricing up a potential deal")
        estimate = self.ensemble.price(deal.product_description)
        discount = estimate - deal.price
        self.log(f"Planning Agent has processed a deal with discount ${discount:.2f}")
        return Opportunity(deal=deal, estimate=estimate, discount=discount)

    def plan(self, memory: List[Opportunity] = []) -> Optional[Opportunity]:
        """
        Run the full workflow:
        1. Use the ScannerAgent to find deals
        2. Use the EnsembleAgent to estimate them
        3. Use the MessagingAgent to send a notification of deals
        :param memory: the opportunities that have been surfaced in the past
        :return: an Opportunity if one was surfaced, otherwise None
        """
        self.log("Planning Agent is kicking off a run")
        selection = self.scanner.scan(memory=memory)
        if selection and selection.deals:
            opportunities = [self.run(deal) for deal in selection.deals[:5]]
            opportunities.sort(key=lambda opp: opp.discount, reverse=True)
            best = opportunities[0]
            self.log(f"Planning Agent has identified the best deal has discount ${best.discount:.2f}")
            if self.is_worth_alerting(best):
                self.messenger.alert(best)
                self.log("Planning Agent has completed a run")
                return best
            self.log("Planning Agent has completed a run - no deal was good enough to alert")
        return None
