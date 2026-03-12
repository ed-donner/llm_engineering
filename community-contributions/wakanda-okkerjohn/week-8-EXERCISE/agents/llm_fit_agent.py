"""LLM-only fit agent: scores how good an opportunity is for a typical indie (no RAG)."""
import re

from agents.agent import Agent
from llm_client import get_client, get_model
from publisher_models import PublisherOpportunity


class LLMFitAgent(Agent):
    """Scores 0-100 based on LLM judgment: indie-friendly, scope, accessibility."""

    name = "LLM Fit Agent"
    color = Agent.MAGENTA

    def __init__(self) -> None:
        self.log("Initializing LLM Fit Agent")
        self._llm = get_client()
        self._model_id = get_model()
        self.log("LLM Fit Agent is ready")

    @staticmethod
    def _parse_score(reply: str) -> float:
        s = reply.replace("$", "").replace(",", "")
        match = re.search(r"\b(\d{1,3}(?:\.\d+)?)\s*(?:/|out of)?\s*100?", s)
        if match:
            return min(100.0, max(0.0, float(match.group(1))))
        match = re.search(r"\b(\d{1,3}(?:\.\d+)?)\b", s)
        if match:
            return min(100.0, max(0.0, float(match.group(1))))
        return 50.0

    def score(self, opportunity: PublisherOpportunity) -> float:
        """
        Score 0-100: how good is this for a typical indie (solo/small team, 6-18 month scope, PC/console)?
        """
        self.log(f"Scoring opportunity: {opportunity.name[:50]}...")
        user_content = (
            "You are evaluating publisher/funding opportunities for indie game developers (solo or small team, 6-18 month projects, PC/console).\n\n"
            "Score from 0 to 100 how good this opportunity is for such a developer: clarity of eligibility, realistic scope, fair terms, and accessibility (no huge barriers).\n\n"
            f"Name: {opportunity.name}\n"
            f"Description: {opportunity.description}\n"
            f"Deadline: {opportunity.deadline}\n"
            + (f"Eligibility: {opportunity.eligibility_summary}\n" if opportunity.eligibility_summary else "")
            + "\nReply with a single number 0-100 (e.g. 72)."
        )
        try:
            response = self._llm.chat.completions.create(
                model=self._model_id,
                messages=[{"role": "user", "content": user_content}],
            )
            reply = response.choices[0].message.content or ""
            score = self._parse_score(reply)
            self.log(f"LLM Fit Agent score: {score:.1f}")
            return score
        except Exception as e:
            self.log(f"OpenRouter/LLM error: {e}; returning 50")
            return 50.0
