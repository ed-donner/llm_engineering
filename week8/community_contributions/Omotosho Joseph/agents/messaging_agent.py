import os
from agents.job_listings import JobOpportunity
from agents.agent import Agent
from litellm import completion
import requests

pushover_url = "https://api.pushover.net/1/messages.json"


class MessagingAgent(Agent):
    name = "Messaging Agent"
    color = Agent.WHITE
    MODEL = "gpt-4o-mini"

    def __init__(self):
        self.log("Messaging Agent is initializing")
        self.pushover_user = os.getenv("PUSHOVER_USER", "")
        self.pushover_token = os.getenv("PUSHOVER_TOKEN", "")
        self.log("Messaging Agent is ready")

    def push(self, text):
        if not self.pushover_user or not self.pushover_token:
            self.log("Pushover not configured - printing alert instead")
            self.log(f"ALERT: {text}")
            return
        self.log("Messaging Agent is sending a push notification")
        payload = {
            "user": self.pushover_user,
            "token": self.pushover_token,
            "message": text,
            "sound": "cashregister",
        }
        requests.post(pushover_url, data=payload)

    def alert(self, opportunity: JobOpportunity):
        text = f"Salary Insight! Offered=${opportunity.listing.salary:,.0f}, "
        text += f"Market Estimate=${opportunity.estimate:,.0f}, "
        text += f"Premium=${opportunity.premium:,.0f}: "
        text += opportunity.listing.job_title[:30] + " at " + opportunity.listing.company[:20]
        text += " " + opportunity.listing.url
        self.push(text)
        self.log("Messaging Agent has completed")

    def craft_message(
        self, description: str, offered_salary: float, estimated_salary: float
    ) -> str:
        user_prompt = (
            "Summarize this job opportunity in 2-3 exciting sentences for a push notification.\n"
            f"Job: {description}\n"
            f"Offered Salary: ${offered_salary:,.0f}\n"
            f"Estimated Market Salary: ${estimated_salary:,.0f}\n\n"
            "Respond only with the 2-3 sentence alert message."
        )
        response = completion(
            model=self.MODEL,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.choices[0].message.content

    def notify(
        self, description: str, offered_salary: float, estimated_salary: float, url: str
    ):
        self.log("Messaging Agent is crafting the notification")
        text = self.craft_message(description, offered_salary, estimated_salary)
        self.push(text[:200] + "... " + url)
        self.log("Messaging Agent has completed")
