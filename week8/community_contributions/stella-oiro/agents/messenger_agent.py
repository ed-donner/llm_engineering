import os
import requests
from agents.base_agent import BaseAgent


class MessengerAgent(BaseAgent):
    """
    Sends Pushover push notifications when an Immediate triage case is identified.
    Set PUSHOVER_USER and PUSHOVER_TOKEN in your .env file.
    If credentials are not set, logs a warning and skips silently.
    """

    color = BaseAgent.RED
    PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

    def __init__(self):
        self.user_key = os.getenv("PUSHOVER_USER")
        self.token = os.getenv("PUSHOVER_TOKEN")
        if self.user_key and self.token:
            self.log("MessengerAgent ready (Pushover configured)")
        else:
            self.log("MessengerAgent: Pushover not configured — notifications disabled")

    def notify(self, presentation: str, triage_level: str, votes: dict) -> bool:
        if triage_level != "Immediate":
            return False  # Only notify for Immediate cases

        title = "IMMEDIATE TRIAGE — See patient NOW"
        message = (
            f"Patient: {presentation[:120]}\n\n"
            f"Decision: IMMEDIATE (life-threatening)\n"
            f"Agent votes: {', '.join(f'{k}: {v}' for k, v in votes.items())}"
        )

        if not (self.user_key and self.token):
            self.log(f"[DRY RUN] Would send: {title} — {message[:80]}")
            return False

        response = requests.post(self.PUSHOVER_URL, data={
            "token":    self.token,
            "user":     self.user_key,
            "title":    title,
            "message":  message,
            "priority": 1,  # high priority — bypasses quiet hours
            "sound":    "siren",
        })

        if response.status_code == 200:
            self.log("Push notification sent to on-call doctor.")
            return True
        else:
            self.log(f"Pushover error: {response.status_code} — {response.text}")
            return False
