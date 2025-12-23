import os
import sys
import http.client
import urllib

w8d5_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if w8d5_path not in sys.path:
    sys.path.insert(0, w8d5_path)

from agents.agent import Agent
from helpers.travel_deals import TravelOpportunity

DO_PUSH = True

class TravelMessagingAgent(Agent):

    name = "Travel Messenger"
    color = Agent.WHITE

    def __init__(self):
        self.log("Travel Messenger initializing")
        if DO_PUSH:
            self.pushover_user = os.getenv('PUSHOVER_USER', 'your-pushover-user-if-not-using-env')
            self.pushover_token = os.getenv('PUSHOVER_TOKEN', 'your-pushover-token-if-not-using-env')
            self.log("Travel Messenger has initialized Pushover")

    def push(self, text):
        self.log("Travel Messenger sending push notification")
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
          urllib.parse.urlencode({
            "token": self.pushover_token,
            "user": self.pushover_user,
            "message": text,
            "sound": "cashregister"
          }), { "Content-type": "application/x-www-form-urlencoded" })
        conn.getresponse()

    def alert(self, opportunity: TravelOpportunity):
        text = f"Travel Deal! {opportunity.deal.destination} - "
        text += f"Price=${opportunity.deal.price:.2f}, "
        text += f"Est=${opportunity.estimate:.2f}, "
        text += f"Save ${opportunity.discount:.2f}! "
        text += opportunity.deal.url
        if DO_PUSH:
            self.push(text)
        self.log("Travel Messenger completed")

