"""
XOF Pricer Agent — API-based price estimation in West African CFA franc (XOF).
Compatible with Week 8 Agent interface; can be used standalone or in an ensemble.
"""
import os
import re
import logging
from .base_agent import Agent
from openai import OpenAI

QUESTION_FR = "Quel est le prix de ce produit en francs CFA (XOF) ? Réponds par un seul nombre."
PREFIX_XOF = "Prix en XOF "


class XOFPricerAgent(Agent):
    name = "XOF Pricer Agent"
    color = Agent.CYAN

    def __init__(self, model: str = "gpt-4o-mini"):
        self.log("Initializing XOF Pricer (API)")
        if os.environ.get("OPENROUTER_API_KEY"):
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.environ["OPENROUTER_API_KEY"],
            )
        else:
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
        self.model = model
        self.log("XOF Pricer Agent ready")

    def price(self, description: str) -> float:
        """Return estimated price in XOF (float)."""
        prompt = f"{QUESTION_FR}\n\n{description}\n\n{PREFIX_XOF}"
        self.log("Calling API for XOF estimate")
        try:
            r = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            text = (r.choices[0].message.content or "").strip()
            value = self._parse_price(text)
            self.log(f"XOF Pricer completed — {value:,.0f} XOF")
            return value
        except Exception as e:
            self.log(f"API error: {e}")
            return 0.0

    @staticmethod
    def _parse_price(reply: str) -> float:
        if not reply:
            return 0.0
        s = str(reply).replace(",", "").replace(" ", "")
        m = re.search(r"[-+]?\d*\.?\d+", s)
        return float(m.group()) if m else 0.0
