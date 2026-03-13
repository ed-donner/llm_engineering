"""
Messaging agent: formats and delivers the best flight opportunity (console and optional push).
Reference: week8 agents/messaging_agent.py
"""

import os
from typing import Optional
import requests

from .agent import Agent
from .flight_deals import FlightOpportunity


class FlightMessagingAgent(Agent):
    """
    Alerts the user about the best flight opportunity. Logs to console;
    optional Pushover push if PUSHOVER_USER and PUSHOVER_TOKEN are set.
    """

    name = "Messaging Agent"
    color = Agent.WHITE

    PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

    def __init__(self):
        self.log("Messaging Agent is initializing")
        self.pushover_user = os.getenv("PUSHOVER_USER")
        self.pushover_token = os.getenv("PUSHOVER_TOKEN")
        self.log("Messaging Agent is ready")

    def _push(self, text: str) -> None:
        if not self.pushover_user or not self.pushover_token:
            return
        self.log("Sending push notification")
        payload = {
            "user": self.pushover_user,
            "token": self.pushover_token,
            "message": text[:1024],
            "sound": "cashregister",
        }
        try:
            requests.post(self.PUSHOVER_URL, data=payload, timeout=5)
        except Exception as e:
            self.log(f"Push failed: {e}")

    def format_opportunity(self, opp: FlightOpportunity) -> str:
        q = opp.quote
        return (
            f"Flight deal #{opp.rank}: {q.route.describe()} — "
            f"${q.price_usd:.2f} USD ({q.source})"
        )

    def alert(self, opportunity: FlightOpportunity) -> None:
        """Log and optionally push the best opportunity."""
        text = self.format_opportunity(opportunity)
        self.log("Alert: " + text)
        self._push("Africa Flight: " + text)
