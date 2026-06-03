import modal
from agents.base_agent import BaseAgent

TRIAGE_LEVELS = ["Immediate", "Urgent", "Semi-urgent", "Non-urgent"]


class SpecialistAgent(BaseAgent):
    """
    Calls the fine-tuned Llama 3.2 3B triage model deployed on Modal.
    Runs fully offline — the Modal service uses only local GPU, no external API.
    """

    color = BaseAgent.RED

    def __init__(self):
        self.log("Connecting to Modal triage service...")
        TriageClassifier = modal.Cls.from_name("clinical-triage-service", "TriageClassifier")
        self.classifier = TriageClassifier()
        self.log("Connected.")

    def classify(self, presentation: str) -> str:
        self.log(f"Classifying: {presentation[:60]}...")
        result = self.classifier.classify.remote(presentation)
        self.log(f"Result: {result}")
        return result if result in TRIAGE_LEVELS else "Unknown"
