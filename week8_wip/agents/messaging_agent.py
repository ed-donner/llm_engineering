import os
from twilio.rest import Client
from agents.deals import Opportunity

class MessagingAgent:

    def __init__(self):
        account_sid = os.getenv('TWILIO_ACCOUNT_SID', 'your-sid-if-not-using-env')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN', 'your-auth-if-not-using-env')
        self.me_from = 'whatsapp:+14155238886'
        self.me_to = f"whatsapp:+1{os.getenv('MY_PHONE_NUMBER', 'your-phone-number-if-not-using-env')}"
        self.client = Client(account_sid, auth_token)

    def message(self, text):
        message = self.client.messages.create(
          from_=self.me_from,
          body=text,
          to=self.me_to
        )

    def alert(self, opportunity: Opportunity):
        text = f"Deal! Price=${opportunity.quality_deal.price:.2f}, "
        text += f"Estimate=${opportunity.estimate:.2f} :"
        text += opportunity.quality_deal.product_description[:10]+'... '
        text += opportunity.quality_deal.url
        self.message(text)
    
        