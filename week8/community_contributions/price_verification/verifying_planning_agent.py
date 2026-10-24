from typing import List, Optional
from agents.deals import Opportunity
from agents.planning_agent import PlanningAgent
from verifier_agent import VerifierAgent


class VerifiedOpportunity(Opportunity):
    """
    An Opportunity whose estimate was replaced by a price found online.
    The estimate the models produced is kept in model_estimate.
    """

    verified: bool = False
    model_estimate: Optional[float] = None


class VerifyingPlanningAgent(PlanningAgent):
    """
    The PlanningAgent with one extra step. Once the best deal of a run has been picked,
    look up what that product currently sells for elsewhere, and measure the discount
    against that price instead of against the estimate. Five deals are estimated,
    only the winner is looked up.
    """

    name = "Verifying Planning Agent"

    def __init__(self, collection):
        super().__init__(collection)
        self.verifier = VerifierAgent()

    def verify(self, opportunity: Opportunity) -> Opportunity:
        """
        Replace the estimate with a real price if one specific product could be identified
        :param opportunity: the opportunity picked as the best of this run
        :returns: the opportunity, verified where a price was found, unchanged otherwise
        """
        lookup = self.verifier.lookup(opportunity.deal.product_description)
        if not lookup:
            self.log("Planning Agent could not verify this price online, so it keeps the estimate")
            return opportunity
        self.log(
            f"Planning Agent verified {lookup.product_name} at ${lookup.price:.2f} at {lookup.retailer} "
            f"from {lookup.count} listing(s) up to ${lookup.highest:.2f}, "
            f"where the models estimated ${opportunity.estimate:.2f}, see {lookup.url}"
        )
        return VerifiedOpportunity(
            deal=opportunity.deal,
            estimate=lookup.price,
            discount=lookup.price - opportunity.deal.price,
            verified=True,
            model_estimate=opportunity.estimate,
        )

    def plan(self, memory: List[str] = []) -> Optional[Opportunity]:
        """
        The same workflow as the PlanningAgent, with the verification step
        between picking the best deal and testing it against the threshold
        :param memory: a list of URLs that have been surfaced in the past
        :return: an Opportunity if one was surfaced, otherwise None
        """
        self.log("Planning Agent is kicking off a run")
        selection = self.scanner.scan(memory=memory)
        if selection:
            opportunities = [self.run(deal) for deal in selection.deals[:5]]
            opportunities.sort(key=lambda opp: opp.discount, reverse=True)
            best = opportunities[0]
            self.log(f"Planning Agent has identified the best deal has discount ${best.discount:.2f}")
            best = self.verify(best)
            if best.discount > self.DEAL_THRESHOLD:
                self.messenger.alert(best)
            self.log("Planning Agent has completed a run")
            return best if best.discount > self.DEAL_THRESHOLD else None
        return None
