from agents.base_agent import BaseAgent
from agents.specialist_agent import SpecialistAgent
from agents.rag_agent import RAGAgent
from agents.frontier_agent import FrontierAgent

TRIAGE_LEVELS = ["Immediate", "Urgent", "Semi-urgent", "Non-urgent"]

# Weights based on observed accuracy: fine-tuned 89%, RAG 85%, frontier 72%
WEIGHTS = {"SpecialistAgent": 0.45, "RAGAgent": 0.35, "FrontierAgent": 0.20}

# Safety rule: if ANY agent says Immediate, escalate to Immediate
# Under-triage of a life-threatening case is worse than over-triage
SAFETY_ESCALATION = True


class EnsembleAgent(BaseAgent):
    """
    Weighted vote across SpecialistAgent, RAGAgent, and FrontierAgent.
    Safety rule: if any agent votes Immediate, the ensemble returns Immediate.
    """

    color = BaseAgent.YELLOW

    def __init__(self, vector_db_path: str = "clinical_vector_db"):
        self.log("Initializing EnsembleAgent...")
        self.specialist = SpecialistAgent()
        self.rag = RAGAgent(vector_db_path)
        self.frontier = FrontierAgent()
        self.log("EnsembleAgent ready.")

    def classify(self, presentation: str) -> tuple[str, dict]:
        self.log(f"Running ensemble for: {presentation[:60]}...")

        votes = {
            "SpecialistAgent": self.specialist.classify(presentation),
            "RAGAgent":        self.rag.classify(presentation),
            "FrontierAgent":   self.frontier.classify(presentation),
        }

        self.log(f"Votes: {votes}")

        # Safety escalation — never under-triage Immediate
        if SAFETY_ESCALATION and "Immediate" in votes.values():
            self.log("Safety escalation: at least one agent voted Immediate.")
            return "Immediate", votes

        # Weighted score per level
        scores = {level: 0.0 for level in TRIAGE_LEVELS}
        for agent_name, vote in votes.items():
            if vote in scores:
                scores[vote] += WEIGHTS[agent_name]

        decision = max(scores, key=scores.get)
        self.log(f"Ensemble decision: {decision} (scores: {scores})")
        return decision, votes
