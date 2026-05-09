"""
Research Planning Agent - orchestrates scanner -> research -> recommendation.
Simplified: no debate, rule-based recommendation from RAG summary.
"""

from typing import List, Optional
from openai import OpenAI

from agents.agent import Agent
from agents.securities_scanner_agent import SecuritiesScannerAgent
from agents.research_agent import ResearchAgent
from models.research import ResearchOpportunity


class ResearchPlanningAgent(Agent):
    name = "Research Planner"
    color = Agent.GREEN
    MODEL = "gpt-4o-mini"

    def __init__(self, collection):
        self.log("Research Planner initializing")
        self.scanner = SecuritiesScannerAgent()
        self.research = ResearchAgent(collection)
        self.client = OpenAI(base_url=self.openrouter_base_url)
        self.log("Research Planner ready")

    def _recommend(self, ticker: str, summary: str) -> tuple:
        """Single LLM call: summary -> buy/hold/sell + confidence."""
        self.log(f"Getting recommendation for {ticker}")
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "user", "content": f"""Based on this research summary for {ticker}, recommend buy, hold, or sell with a confidence score 0-1.

Summary:
{summary[:1500]}

Reply with exactly: RECOMMENDATION|CONFIDENCE
Example: hold|0.65"""},
            ],
            max_tokens=20,
        )
        text = response.choices[0].message.content.strip().lower()
        try:
            rec, conf = text.split("|")
            rec = rec.strip()[:4]  # buy, hold, sell
            conf = float(conf.strip())
            rec = "buy" if "buy" in rec else "sell" if "sell" in rec else "hold"
            return rec, min(1, max(0, conf))
        except Exception:
            return "hold", 0.5

    def plan(self, memory: List[str] = None) -> Optional[ResearchOpportunity]:
        memory = memory or []
        events = self.scanner.scan(memory=memory)
        if not events:
            self.log("No events to research")
            return None

        event = events[0]
        self.log(f"Researching {event.ticker}")
        summary = self.research.research(event.ticker, focus="investment outlook")
        rec, conf = self._recommend(event.ticker, summary)

        opp = ResearchOpportunity(
            ticker=event.ticker,
            recommendation=rec,
            confidence=conf,
            summary=summary[:500],
            url=event.source_url,
        )
        self.log(f"Research Planner completed for {event.ticker}")
        return opp
