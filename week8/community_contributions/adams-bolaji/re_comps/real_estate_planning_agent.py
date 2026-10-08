"""
RealEstatePlanningAgent - Orchestrates Scanner, Comps, and Messaging.
"""
from typing import List, Optional
from agents.agent import Agent

import sys
from pathlib import Path

adams_path = Path(__file__).resolve().parent.parent  # adams-bolaji
if str(adams_path) not in sys.path:
    sys.path.insert(0, str(adams_path))

from models import Listing, ListingSelection, PropertyOpportunity
from re_comps.comps_agent import CompsAgent
from re_comps.listing_scanner_agent import ListingScannerAgent


# Optional: use week8 MessagingAgent if PUSHOVER is configured
def _get_messaging_agent():
    try:
        from agents.messaging_agent import MessagingAgent
        return MessagingAgent()
    except Exception:
        return None


class RealEstateMessagingAgent(Agent):
    """Sends alerts for property opportunities. Uses Pushover if configured."""

    name = "Real Estate Messaging Agent"
    color = Agent.WHITE

    def __init__(self):
        self.log("Real Estate Messaging Agent is initializing")
        self._pushover = _get_messaging_agent()
        self.log("Real Estate Messaging Agent is ready")

    def alert(self, opportunity: PropertyOpportunity):
        """Send notification about a property opportunity."""
        opp = opportunity
        text = (
            f"Property Deal! List: ${opp.listing.price:,.0f} "
            f"Est: ${opp.estimate:,.0f} "
            f"Discount: ${opp.discount:,.0f} — "
            f"{opp.listing.product_description[:60]}... {opp.listing.url}"
        )
        if self._pushover:
            self._pushover.push(text)
        else:
            self.log(f"[Console Alert] {text}")
        self.log("Real Estate Messaging Agent has sent alert")


class RealEstatePlanningAgent(Agent):
    """
    Plans the workflow: scan listings -> estimate via comps -> alert on good deals.
    """

    name = "Real Estate Planning Agent"
    color = Agent.GREEN
    DEAL_THRESHOLD = 25000  # Minimum discount to consider a deal ($)

    def __init__(self, collection):
        self.log("Real Estate Planning Agent is initializing")
        self.scanner = ListingScannerAgent()
        self.comps = CompsAgent(collection)
        self.messenger = RealEstateMessagingAgent()
        self.log("Real Estate Planning Agent is ready")

    def run(self, listing: Listing) -> PropertyOpportunity:
        """Estimate a listing's value and compute discount."""
        self.log("Real Estate Planning Agent is estimating a listing")
        estimate = self.comps.estimate(listing.product_description)
        discount = estimate - listing.price
        self.log(f"Real Estate Planning Agent: estimate=${estimate:,.0f}, discount=${discount:,.0f}")
        return PropertyOpportunity(listing=listing, estimate=estimate, discount=discount)

    def plan(self, memory: List[PropertyOpportunity] = None) -> Optional[PropertyOpportunity]:
        """
        Full workflow: scan -> estimate each -> pick best -> alert if above threshold.
        """
        memory = memory or []
        self.log("Real Estate Planning Agent is scanning for listings")
        selection = self.scanner.scan(memory=memory)

        if not selection or not selection.listings:
            self.log("Real Estate Planning Agent: No new listings")
            return None

        opportunities = [self.run(listing) for listing in selection.listings[:5]]
        opportunities.sort(key=lambda o: o.discount, reverse=True)
        best = opportunities[0]

        self.log(f"Real Estate Planning Agent: best discount ${best.discount:,.0f}")

        if best.discount > self.DEAL_THRESHOLD:
            self.messenger.alert(best)

        self.log("Real Estate Planning Agent has completed")
        return best if best.discount > self.DEAL_THRESHOLD else None
