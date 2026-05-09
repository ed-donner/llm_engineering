import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

class MessengerAgent:
    """
    MessengerAgent using Pushover API to send push notifications to a user's phone.
    """
    def __init__(self):
        self.pushover_user = os.getenv('PUSHOVER_USER')
        self.pushover_token = os.getenv('PUSHOVER_TOKEN')
        self.pushover_url = "https://api.pushover.net/1/messages.json"
        
        if not self.pushover_user or not self.pushover_token:
            print("Warning: PUSHOVER_USER or PUSHOVER_TOKEN not found in .env file.")

    def push(self, title: str, message: str) -> str:
        """
        Sends a push notification to the user's phone via Pushover.
        """
        print(f"Pushing message: {title}")
        if not self.pushover_user or not self.pushover_token:
             return "Failed: Missing Pushover credentials."
             
        payload = {
            "user": self.pushover_user, 
            "token": self.pushover_token, 
            "title": title,
            "message": message
        }
        
        try:
            response = requests.post(self.pushover_url, data=payload)
            response.raise_for_status()
            return "Push notification sent successfully."
        except requests.RequestException as e:
            return f"Error sending push notification: {e}"

if __name__ == "__main__":
    messenger = MessengerAgent()
    print(messenger.push("Tech Analogy Alert", "This is a test message from your Agent!"))
