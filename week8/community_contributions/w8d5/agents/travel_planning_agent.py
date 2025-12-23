import os
import sys
from typing import Optional, List

w8d5_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if w8d5_path not in sys.path:
    sys.path.insert(0, w8d5_path)

from agents.agent import Agent
from helpers.travel_deals import TravelDeal, TravelOpportunity
from agents.travel_scanner_agent import TravelScannerAgent
from agents.travel_estimator_agent import TravelEstimatorAgent
from agents.travel_messaging_agent import TravelMessagingAgent


class TravelPlanningAgent(Agent):

    name = "Travel Planner"
    color = Agent.GREEN
    DEAL_THRESHOLD = 50

    def __init__(self, collection):
        self.log("Travel Planner initializing")
        self.scanner = TravelScannerAgent()
        self.estimator = TravelEstimatorAgent(collection)
        self.messenger = TravelMessagingAgent()
        self.log("Travel Planner ready")

    def evaluate(self, deal: TravelDeal) -> TravelOpportunity:
        self.log(f"Travel Planner evaluating {deal.destination}")
        estimate = self.estimator.estimate(deal.description)
        discount = estimate - deal.price
        self.log(f"Travel Planner found discount ${discount:.2f}")
        return TravelOpportunity(deal=deal, estimate=estimate, discount=discount)

    def plan(self, memory: List[str] = []) -> Optional[List[TravelOpportunity]]:
        self.log("Travel Planner starting run")
        selection = self.scanner.scan(memory=memory)
        if selection and selection.deals:
            opportunities = [self.evaluate(deal) for deal in selection.deals[:5]]
            if not opportunities:
                self.log("Travel Planner found no valid opportunities")
                return None
            opportunities.sort(key=lambda opp: opp.discount, reverse=True)
            good_deals = [opp for opp in opportunities if opp.discount > self.DEAL_THRESHOLD]
            if good_deals:
                best = good_deals[0]
                self.log(f"Travel Planner found {len(good_deals)} deals above threshold, best: ${best.discount:.2f} off")
                self.messenger.alert(best)
                self.log("Travel Planner completed")
                return good_deals
            else:
                self.log(f"Travel Planner completed - no deals above ${self.DEAL_THRESHOLD} threshold")
                return None
        self.log("Travel Planner found no deals to evaluate")
        return None

