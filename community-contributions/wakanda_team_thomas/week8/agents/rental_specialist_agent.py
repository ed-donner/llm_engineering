import modal
from agents.agent import Agent
from agents.rental_deals import RentalDeal


class RentalSpecialistAgent(Agent):
    """Estimates fair rent using a fine-tuned Llama model deployed on Modal."""

    name = "Specialist"
    color = "magenta"

    def __init__(self):
        self.pricer = modal.Function.from_name("rental-pricer-service", "estimate_rent")

    def estimate(self, deal: RentalDeal) -> float:
        self.log(f"Calling fine-tuned model on Modal for: {deal.title}")
        description = self._format_input(deal)
        result = self.pricer.remote(description)
        estimate = float(result)
        self.log(f"Specialist estimate: ${estimate:,.2f}/month")
        return estimate

    def _format_input(self, deal: RentalDeal) -> str:
        return (
            f"{deal.bedrooms}-bedroom, {deal.sqft} sqft in {deal.city}. "
            f"{deal.description}"
        )
