import os
import anthropic
import requests
from agents.deals import Opportunity
from agents.agent import Agent


class MessagingAgent(Agent):
    """
    An Agent that sends deal alerts to your phone through a Telegram bot
    """

    name = "Messaging Agent"
    color = Agent.WHITE
    MODEL = "claude-sonnet-5"

    def __init__(self):
        """
        Set up this object with the Telegram bot token and chat ID from the .env file
        """
        self.log("Messaging Agent is initializing")
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.telegram_url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        self.claude = anthropic.Anthropic()
        self.log("Messaging Agent has initialized Telegram and Claude")

    def push(self, text):
        """
        Send a message to your Telegram chat
        """
        self.log("Messaging Agent is sending a Telegram message")
        payload = {"chat_id": self.telegram_chat_id, "text": text}
        response = requests.post(self.telegram_url, data=payload, timeout=30).json()
        if not response.get("ok"):
            self.log(f"Telegram did not accept the message: {response.get('description')}")

    def alert(self, opportunity: Opportunity):
        """
        Make an alert about the specified Opportunity
        """
        text = f"Deal Alert! Price=${opportunity.deal.price:.2f}, "
        text += f"Estimate=${opportunity.estimate:.2f}, "
        text += f"Discount=${opportunity.discount:.2f} : "
        text += opportunity.deal.product_description[:80] + "... "
        text += opportunity.deal.url
        self.push(text)
        self.log("Messaging Agent has completed")

    def craft_message(self, description: str, deal_price: float, estimated_true_value: float) -> str:
        user_prompt = "Please summarize this great wine deal in 2-3 sentences to be sent as an exciting message alerting the user about this deal.\n"
        user_prompt += f"Wine Description: {description}\nOffered Price: {deal_price}\nEstimated true value: {estimated_true_value}"
        user_prompt += "\n\nRespond only with the 2-3 sentence message which will be used to alert & excite the user about this deal"
        response = self.claude.messages.create(
            model=self.MODEL,
            max_tokens=16000,
            messages=[{"role": "user", "content": user_prompt}],
            extra_body={"output_config": {"effort": "low"}},
        )
        return next((block.text for block in response.content if block.type == "text"), "")

    def notify(self, description: str, deal_price: float, estimated_true_value: float, url: str):
        """
        Make an alert about the specified details, with the message written by Claude
        """
        self.log("Messaging Agent is using Claude to craft the message")
        text = self.craft_message(description, deal_price, estimated_true_value)
        self.push(text[:400] + "... " + url)
        self.log("Messaging Agent has completed")
