"""
Planning agent: orchestrates scanner → pricer → ranking and returns best opportunity.
Reference: week8 agents/planning_agent.py
"""

from typing import List, Optional

from .agent import Agent
from .flight_deals import FlightRoute, FlightQuote, FlightOpportunity
from .route_scanner_agent import RouteScannerAgent
from .flight_pricer_agent import FlightPricerAgent
from .messaging_agent import FlightMessagingAgent


class FlightPlanningAgent(Agent):
    """
    Coordinates the multi-agent flow: scan routes → price each → rank → notify best.
    """

    name = "Planning Agent"
    color = Agent.GREEN

    def __init__(
        self,
        scanner: Optional[RouteScannerAgent] = None,
        pricer: Optional[FlightPricerAgent] = None,
        messenger: Optional[FlightMessagingAgent] = None,
    ):
        self.log("Planning Agent is initializing")
        self.scanner = scanner or RouteScannerAgent()
        self.pricer = pricer or FlightPricerAgent()
        self.messenger = messenger or FlightMessagingAgent()
        self.log("Planning Agent is ready")

    def run_for_routes(self, routes: List[FlightRoute]) -> List[FlightOpportunity]:
        """Price each route, sort by price (ascending), return opportunities with rank."""
        if not routes:
            self.log("No routes to process")
            return []
        self.log(f"Pricing {len(routes)} routes")
        quotes = [self.pricer.price(r) for r in routes]
        quotes = [q for q in quotes if q.price_usd > 0]
        quotes.sort(key=lambda q: q.price_usd)
        opportunities = [
            FlightOpportunity(quote=q, rank=i + 1, message=f"Rank {i + 1} by price")
            for i, q in enumerate(quotes)
        ]
        self.log(f"Best price: ${quotes[0].price_usd:.2f} for {quotes[0].route.describe()}")
        return opportunities

    def plan(
        self,
        memory_seen: Optional[List[str]] = None,
        user_query: Optional[str] = None,
        notify_best: bool = True,
    ) -> Optional[FlightOpportunity]:
        """
        Full autonomous run: scan → price → rank → optionally notify best deal.
        Returns the best opportunity (lowest price in the batch), or None if no routes.
        """
        self.log("Planning Agent starting a run")
        routes = self.scanner.scan(memory_urls=memory_seen, user_query=user_query)
        if not routes:
            self.log("No routes from scanner; run complete")
            return None
        opportunities = self.run_for_routes(routes)
        if not opportunities:
            self.log("No valid quotes; run complete")
            return None
        best = opportunities[0]
        if notify_best:
            self.messenger.alert(best)
        self.log("Planning Agent run complete")
        return best
