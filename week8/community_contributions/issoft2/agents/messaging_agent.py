import os
from agents.deals import Opportunity
import http.client
import urllib
from agents.agent import Agent


class MessagingAgent(Agent):

    name = "Messaging Agent"
    color = Agent.WHITE

    def __init__(self):
        """
        Set up this object to either do push notifications via Pushover,
        or SMS via Twilio,
        whichever is specified in the constants
        """
        # Used push over api
        self.pushover_user = os.getenv('PUSHOVER_USER')
        self.pushover_token = os.getenv('PUSHOVER_TOKEN')
        self.log("Messaging Agent has initialized Pushover")

    def push(self, text):
        """
        Send a Push Notification using the Pushover API
        """
        self.log("Messaging Agent is sending a push notification")
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
          urllib.parse.urlencode({
            "token": self.pushover_token,
            "user": self.pushover_user,
            "message": text,
            "sound": "cashregister"
          }), { "Content-type": "application/x-www-form-urlencoded" })
        conn.getresponse()

    def alert(self, opportunity: Opportunity):
        """
        Make an alert about the specified Opportunity
        """
        text = f"Deal Alert! Price=${opportunity.deal.price:.2f}, "
        text += f"Estimate=${opportunity.estimate:.2f}, "
        text += f"Discount=${opportunity.discount:.2f} :"
        text += opportunity.deal.product_description[:10]+'... '
        text += opportunity.deal.url
        self.push(text)
        self.log("Messaging Agent has completed")
        
    
        