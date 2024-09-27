from agents.deals import Deal, QualityDealSelection, Opportunity

from agents.scanner_agent import ScannerAgent
from agents.ensemble_agent import EnsembleAgent
from agents.messaging_agent import MessagingAgent


class PlanningAgent:

    def __init__(self, collection):
        self.scanner = ScannerAgent()
        self.ensemble = EnsembleAgent(collection)
        self.messenger = MessagingAgent()

    def plan(self):
        opportunities = []
        deal_selection = self.scanner.scan()
        for deal in deal_selection.quality_deals[:5]:
            estimate = self.ensemble.price(deal.product_description)
            opportunities.append(Opportunity(deal, estimate, estimate - deal.price))
        opportunities.sort(key=lambda opp: opp.discount, reverse=True)
        print(opportunities)
        if opportunities[0].discount > 50:
            self.messenger.alert(opportunities[0])