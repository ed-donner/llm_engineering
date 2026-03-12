import modal
from agents.agent import Agent


class SpecialistAgent(Agent):
    """
    Calls the fine-tuned salary prediction LLM running remotely on Modal.
    Mirrors the course's SpecialistAgent but for salary estimation.
    """

    name = "Specialist Agent"
    color = Agent.RED

    def __init__(self):
        self.log("Specialist Agent is initializing - connecting to Modal")
        SalaryPredictor = modal.Cls.from_name("salary-service", "SalaryPredictor")
        self.predictor = SalaryPredictor()

    def estimate(self, description: str) -> float:
        """
        Make a remote call to estimate the salary for this job description.
        """
        self.log("Specialist Agent is calling remote fine-tuned model")
        result = self.predictor.estimate.remote(description)
        self.log(f"Specialist Agent completed - predicting ${result:,.0f}")
        return result
