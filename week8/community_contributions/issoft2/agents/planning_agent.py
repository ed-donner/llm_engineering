from typing import Optional, List
from agents.agent import Agent
from agents.deals import Deal, Opportunity
from agents.scanner_agent import ScannerAgent
from agents.messaging_agent import MessagingAgent
from agents.ensemble_agent import EnsembleAgent


class PlanningAgent(Agent):
    name = "Planning Agent"
    color = Agent.GREEN
    DEAL_THRESHOLD = 50

    def __init__(self, collection):
        """
        Create instance of the 3 Agents that his planner coordinates
        """
        self.log("Planning Agent is initializing")
        self.scanner = ScannerAgent()
        self.ensemble = EnsembleAgent(collection)
        self.messenger = MessagingAgent()
        self.log("Planning Agent is ready")

    def run(self, deal: Deal) -> Opportunity:
        """
        Run the worflow for a particular deal
        :param deal: the deal, summarized from an RSS scrape
        :returns: an opportunity including the discount
        """

        self.log("Planning Agent is pricing up a potential deal")
        estimate = self.ensemble.price(deal.product_description)
        discount = estimate - deal.price 
        self.log(f"Planning Agent has proccessed a deal with discount ${discount:.2f}")
        return Optional(deal=deal, estimate=estimate, discount=discount)


    def plan(self, memory: List[str] = []) -> Optional[Opportunity]:
        """
        Run the full worklflow:
        1. Use the ScannerAgent to find deals from RSS feeds
        2. Use the EnsembleAgent to find estimate them
        3. Use the MessagingAgent to send a notification of deals
        :param memory: a list of URLs that have been surfaced in the past
        :return: an Opportunity if one was surfaced, otherwise None
        """
        self.log("Planning Agent is starting off a run")
        selection = self.scanner.scan(memory=memory)
        if selection:
            Opportunities = [self.run(deal) for deal in selection.deals[:5]]
            Opportunities.sort(key=lambda opp: opp.discount, reverse=True)
            best = Opportunities[0]
            self.log(f"Planning Agent has identified the best deal has discount ${best.discount:.2f}")
            if best.discount > self.DEAL_THRESHOLD:
                self.messenger.alert(best)
            self.log("Planning Agent has completed a run")
            return best if best.discount > self.DEAL_THRESHOLD else None

        return None    

