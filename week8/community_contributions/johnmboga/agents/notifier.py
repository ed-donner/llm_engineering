"""
agents/notifier.py
Agent 4: Pushover Notification Agent
Sends a formatted push notification via the Pushover API
whenever a job match is found above the fit threshold.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"


class Notifier:
    """Sends job-match notifications via the Pushover API."""

    def __init__( self ):
        self._user_key = os.getenv("PUSHOVER_USER")
        self._app_token = os.getenv("PUSHOVER_TOKEN")

    @staticmethod
    def _priority(score: float) -> int:
        """
        Map fit score to Pushover priority:
        -1 = quiet  (no sound)
         0 = normal
         1 = high   (bypass quiet hours)
        """
        if score >= 85:
            return 1
        elif score >= 70:
            return 0
        return -1

    def send_notification(self, match: dict, seeker_name: str = "Job Seeker") -> bool:
        """
        Send a Pushover notification for a job match.

        Args:
            match: dict with keys title, company, score, summary, url
            seeker_name: identifier for the job seeker (shown in notification)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self._user_key or not self._app_token:
            print("[Notifier] Missing Pushover credentials — skipping notification")
            return False

        title = f"🎯 {match['score']}% Match — {match['title']}"
        message = (
            f"👤 Seeker: {seeker_name}\n"
            f"🏢 Company: {match['company']}\n\n"
            f"💡 {match.get('summary', 'Strong match based on your profile.')}\n\n"
            f"🔗 {match['url']}"
        )

        payload = {
            "token": self._app_token,
            "user": self._user_key,
            "title": title,
            "message": message,
            "priority": self._priority(match["score"]),
            "url": match["url"],
            "url_title": "View Job Listing",
            "sound": "magic",
        }

        try:
            resp = requests.post(PUSHOVER_API_URL, data=payload, timeout=10)
            resp.raise_for_status()
            print(f"[Notifier] ✅ Notification sent: {title}")
            return True
        except requests.RequestException as e:
            print(f"[Notifier] ❌ Failed to send notification: {e}")
            return False
