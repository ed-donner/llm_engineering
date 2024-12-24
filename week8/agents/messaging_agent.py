import os
from twilio.rest import Client
from agents.deals import Opportunity
import http.client
import urllib
from agents.agent import Agent


DO_TEXT = False
DO_PUSH = True

class MessagingAgent(Agent):

    name = "Agente de Mensajería"
    color = Agent.WHITE

    def __init__(self):
        """
        Configure este objeto para que envíe notificaciones push a través de Pushover,
        o SMS a través de Twilio,
        lo que se especifique en las constantes
        """
        self.log(f"Inicializando Agente de Mensajería")
        if DO_TEXT:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID', 'your-sid-if-not-using-env')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN', 'your-auth-if-not-using-env')
            self.me_from = os.getenv('TWILIO_FROM', 'your-phone-number-if-not-using-env')
            self.me_to = os.getenv('MY_PHONE_NUMBER', 'your-phone-number-if-not-using-env')
            self.client = Client(account_sid, auth_token)
            self.log("El agente de mensajería ha iniciado Twilio")
        if DO_PUSH:
            self.pushover_user = os.getenv('PUSHOVER_USER', 'your-pushover-user-if-not-using-env')
            self.pushover_token = os.getenv('PUSHOVER_TOKEN', 'your-pushover-user-if-not-using-env')
            self.log("El agente de mensajería ha iniciado Pushover")

    def message(self, text):
        """
        Envía un mensaje SMS mediante la API de Twilio
        """
        self.log("Agente de Mensajería enviando mensaje de texto")
        message = self.client.messages.create(
          from_=self.me_from,
          body=text,
          to=self.me_to
        )

    def push(self, text):
        """
        Envía una Push Notification mediante la API de Pushover
        """
        self.log("Agente de Mensajería enviando una push notification")
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
        Crear una alerta sobre la oportunidad especificada
        """
        text = f"Alerta de Oferta! Precio=${opportunity.deal.price:.2f}, "
        text += f"Precio Estimado=${opportunity.estimate:.2f}, "
        text += f"Descuento=${opportunity.discount:.2f} :"
        text += opportunity.deal.product_description[:10]+'... '
        text += opportunity.deal.url
        if DO_TEXT:
            self.message(text)
        if DO_PUSH:
            self.push(text)
        self.log("Agente de Mensajería completado")
        
    
        