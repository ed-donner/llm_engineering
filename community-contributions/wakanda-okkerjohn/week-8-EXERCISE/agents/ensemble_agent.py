"""Ensemble: combines RAG fit and LLM fit into one score."""
from agents.agent import Agent
from agents.publisher_fit_agent import PublisherFitAgent
from agents.llm_fit_agent import LLMFitAgent
from publisher_models import PublisherOpportunity, ScoredOpportunity


class EnsembleAgent(Agent):
    """Combines PublisherFitAgent (RAG) and LLMFitAgent into a single 0-100 fit score."""

    name = "Ensemble Agent"
    color = Agent.YELLOW
    RAG_WEIGHT = 0.6
    LLM_WEIGHT = 0.4

    def __init__(self) -> None:
        self.log("Initializing Ensemble Agent")
        self.rag_fit = PublisherFitAgent()
        self.llm_fit = LLMFitAgent()
        self.log("Ensemble Agent is ready")

    def score(self, opportunity: PublisherOpportunity) -> ScoredOpportunity:
        rag_s = self.rag_fit.score(opportunity)
        llm_s = self.llm_fit.score(opportunity)
        combined = rag_s * self.RAG_WEIGHT + llm_s * self.LLM_WEIGHT
        self.log(f"Ensemble score: {combined:.1f} (RAG={rag_s:.1f}, LLM={llm_s:.1f})")
        return ScoredOpportunity(opportunity=opportunity, fit_score=round(combined, 1))
