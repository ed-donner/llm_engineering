import os
import requests
from openai import OpenAI
from agents.agent import Agent
from agents.rental_deals import RentalOpportunity


class RentalMessagingAgent(Agent):
    """Crafts alert messages with GPT and sends push notifications via Pushover."""

    name = "Messenger"
    color = "blue"

    PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

    SYSTEM_PROMPT = """You write short, compelling rental deal alerts. Given a rental opportunity,
write a 2-3 sentence notification message highlighting the deal. Include the neighborhood,
price, estimated value, and monthly savings. Be direct and informative."""

    def __init__(self):
        self.client = OpenAI()
        self.pushover_token = os.getenv("PUSHOVER_TOKEN")
        self.pushover_user = os.getenv("PUSHOVER_USER")

    def alert(self, opportunity: RentalOpportunity):
        self.log(f"Preparing alert for: {opportunity.deal.title}")
        message = self._craft_message(opportunity)
        self.log(f"Message: {message}")

        if self.pushover_token and self.pushover_user:
            self._send_pushover(message, opportunity.deal.url)
            self.log("Push notification sent.")
        else:
            self.log("Pushover not configured. Skipping push notification.")

    def _craft_message(self, opportunity: RentalOpportunity) -> str:
        deal = opportunity.deal
        prompt = (
            f"Rental deal found:\n"
            f"Title: {deal.title}\n"
            f"City: {deal.city}\n"
            f"Listed rent: ${deal.rent:,.2f}/month\n"
            f"Estimated fair rent: ${opportunity.estimated_fair_rent:,.2f}/month\n"
            f"Monthly savings: ${opportunity.monthly_savings:,.2f}\n"
            f"Bedrooms: {deal.bedrooms}, Size: {deal.sqft} sqft\n"
            f"URL: {deal.url}"
        )

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=200,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0].message.content

    def _send_pushover(self, message: str, url: str):
        requests.post(self.PUSHOVER_URL, data={
            "token": self.pushover_token,
            "user": self.pushover_user,
            "message": message,
            "url": url,
            "title": "Rental Deal Alert",
        })
