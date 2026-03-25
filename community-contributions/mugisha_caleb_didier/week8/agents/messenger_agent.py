import os
import requests
from agents.agent import Agent
from litellm import completion


class MessengerAgent(Agent):

    name = "Messenger Agent"
    color = Agent.WHITE
    MODEL = "gpt-4.1-mini"

    def __init__(self):
        self.log("Initializing")
        self.pushover_user = os.getenv("PUSHOVER_USER")
        self.pushover_token = os.getenv("PUSHOVER_TOKEN")
        if self.pushover_user and self.pushover_token:
            self.log("Pushover configured")
        else:
            self.log("No Pushover keys - alerts will be logged only")

    def push(self, text: str):
        if self.pushover_user and self.pushover_token:
            self.log("Sending push notification via Pushover")
            try:
                requests.post(
                    "https://api.pushover.net/1/messages.json",
                    data={
                        "user": self.pushover_user,
                        "token": self.pushover_token,
                        "message": text,
                        "sound": "cosmic",
                    },
                )
            except Exception as e:
                self.log(f"Pushover error: {e}")
        else:
            self.log(f"[No Pushover] Would send: {text[:120]}...")

    def craft_message(self, title: str, summary: str, importance: float) -> str:
        prompt = (
            "Write a 2-sentence push notification about this important tech story. "
            "Be concise and informative, no hype.\n\n"
            f"Title: {title}\nSummary: {summary}\nImportance: {importance}/10"
        )
        response = completion(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    def notify(self, title: str, summary: str, importance: float, url: str):
        self.log(f"Crafting notification for: {title[:50]}...")
        text = self.craft_message(title, summary, importance)
        msg = f"{text[:180]}\n{url}"
        self.push(msg)
        self.log("Notification complete")
