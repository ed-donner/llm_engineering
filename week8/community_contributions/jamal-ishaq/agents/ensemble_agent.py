from typing import Dict
from urllib.parse import urlparse

from agents.agent import Agent
from agents.resources import ResourceOpportunity, ScannedResource


class EnsembleAgent(Agent):
    name = "Ensemble Agent"
    color = Agent.YELLOW

    TRUSTED_DOMAINS = {
        "platform.openai.com": 35.0,
        "openai.com": 35.0,
        "arxiv.org": 32.0,
        "github.com": 28.0,
        "python.langchain.com": 26.0,
        "huggingface.co": 24.0,
    }

    KEYWORD_WEIGHTS = {
        "evaluation": 12.0,
        "benchmark": 9.0,
        "agent": 8.0,
        "tool": 6.0,
        "framework": 6.0,
        "tutorial": 5.0,
        "guide": 4.0,
    }

    def __init__(self):
        self.log("Initializing Ensemble Agent")
        self.log("Ensemble Agent is ready")

    def _domain_score(self, url: str) -> float:
        domain = urlparse(url).netloc
        return self.TRUSTED_DOMAINS.get(domain, 15.0)

    def _keyword_score(self, text: str) -> float:
        score = 0.0
        lower = text.lower()
        for keyword, weight in self.KEYWORD_WEIGHTS.items():
            if keyword in lower:
                score += weight
        return min(score, 40.0)

    def _richness_score(self, snippet: str) -> float:
        length = len(snippet.strip())
        if length > 260:
            return 15.0
        if length > 160:
            return 10.0
        if length > 80:
            return 6.0
        return 2.0

    def score(self, resource: ScannedResource, topic: str) -> ResourceOpportunity:
        self.log("Scoring candidate resource")
        combined_text = f"{resource.title} {resource.snippet} {topic}"
        domain_score = self._domain_score(resource.url)
        keyword_score = self._keyword_score(combined_text)
        richness_score = self._richness_score(resource.snippet)
        estimated_quality = round(domain_score + keyword_score + richness_score, 2)
        value_gap = round(estimated_quality - 50.0, 2)
        breakdown: Dict[str, float] = {
            "domain_score": domain_score,
            "keyword_score": keyword_score,
            "richness_score": richness_score,
        }
        return ResourceOpportunity(
            resource=resource,
            estimated_quality=estimated_quality,
            value_gap=value_gap,
            score_breakdown=breakdown,
        )
