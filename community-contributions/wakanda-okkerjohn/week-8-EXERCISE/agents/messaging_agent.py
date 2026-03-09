"""Messaging agent: sends push alerts for high-fit opportunities."""
import os
from typing import Optional

import requests

from agents.agent import Agent
from publisher_models import ScoredOpportunity

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"


class MessagingAgent(Agent):
    name = "Messaging Agent"
    color = Agent.WHITE

    def __init__(self) -> None:
        self.log("Messaging Agent is initializing")
        self.pushover_user = os.getenv("PUSHOVER_USER", "")
        self.pushover_token = os.getenv("PUSHOVER_TOKEN", "")
        self.log("Messaging Agent is ready")

    def push(self, text: str) -> None:
        """Send a push notification via Pushover (no-op if credentials missing)."""
        if not self.pushover_user or not self.pushover_token:
            self.log("Pushover not configured (PUSHOVER_USER/PUSHOVER_TOKEN); skipping push")
            return
        payload = {
            "user": self.pushover_user,
            "token": self.pushover_token,
            "message": text[:1024],
            "sound": "intermission",
        }
        try:
            requests.post(PUSHOVER_URL, data=payload, timeout=10)
            self.log("Push notification sent")
        except Exception as e:
            self.log(f"Push failed: {e}")

    def alert(self, scored: ScoredOpportunity) -> None:
        """Send an alert for a high-fit publisher/funding opportunity."""
        o = scored.opportunity
        text = (
            f"Publisher/fund match (fit {scored.fit_score:.0f}/100): {o.name}\n"
            f"Deadline: {o.deadline}\n{o.url}"
        )
        self.push(text)
        self.log("Messaging Agent has completed alert")
