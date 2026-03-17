from agents.agent import Agent
from agents.rental_deals import RentalDeal
from agents.rental_frontier_agent import RentalFrontierAgent
from agents.rental_specialist_agent import RentalSpecialistAgent


class RentalEnsembleAgent(Agent):
    """Combines estimates from Frontier, Specialist, and Neural Network agents using weighted average."""

    name = "Ensemble"
    color = "yellow"

    WEIGHTS = {
        "frontier": 0.80,
        "specialist": 0.10,
        "neural_net": 0.10,
    }

    def __init__(self, frontier: RentalFrontierAgent, specialist: RentalSpecialistAgent, neural_net_fn=None):
        self.frontier = frontier
        self.specialist = specialist
        self.neural_net_fn = neural_net_fn

    def estimate(self, deal: RentalDeal) -> float:
        self.log(f"Running ensemble estimation for: {deal.title}")

        frontier_est = self.frontier.estimate(deal)
        self.log(f"Frontier: ${frontier_est:,.2f}")

        if self.specialist:
            try:
                specialist_est = self.specialist.estimate(deal)
            except Exception as e:
                self.log(f"Specialist failed ({e}), using Frontier as fallback.")
                specialist_est = frontier_est
        else:
            specialist_est = frontier_est
            self.log("Specialist not available, using Frontier as fallback.")
        self.log(f"Specialist: ${specialist_est:,.2f}")

        if self.neural_net_fn:
            try:
                nn_est = self.neural_net_fn(deal)
            except Exception as e:
                self.log(f"Neural network failed ({e}), using Frontier as fallback.")
                nn_est = frontier_est
        else:
            nn_est = frontier_est
            self.log("Neural network not available, using Frontier as fallback.")
        self.log(f"Neural Net: ${nn_est:,.2f}")

        estimate = (
            self.WEIGHTS["frontier"] * frontier_est
            + self.WEIGHTS["specialist"] * specialist_est
            + self.WEIGHTS["neural_net"] * nn_est
        )

        self.log(f"Ensemble estimate: ${estimate:,.2f}/month")
        return estimate
