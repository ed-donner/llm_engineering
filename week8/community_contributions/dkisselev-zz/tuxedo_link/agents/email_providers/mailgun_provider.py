"""Mailgun email provider implementation."""

import os
import requests
import logging
from typing import Optional
from .base import EmailProvider
from utils.config import get_mailgun_config, get_email_config


logger = logging.getLogger(__name__)


class MailgunProvider(EmailProvider):
    """Mailgun email provider."""
    
    def __init__(self):
        """Initialize Mailgun provider."""
        self.api_key = os.getenv('MAILGUN_API_KEY')
        if not self.api_key:
            raise ValueError("MAILGUN_API_KEY environment variable not set")
        
        mailgun_config = get_mailgun_config()
        self.domain = mailgun_config['domain']
        self.base_url = f"https://api.mailgun.net/v3/{self.domain}/messages"
        
        email_config = get_email_config()
        self.default_from_name = email_config['from_name']
        self.default_from_email = email_config['from_email']
        
        logger.info(f"Mailgun provider initialized with domain: {self.domain}")
    
    def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """
        Send an email via Mailgun.
        
        Args:
            to: Recipient email address
            subject: Email subject
            html: HTML body
            text: Plain text body
            from_email: Sender email (optional, uses config default)
            from_name: Sender name (optional, uses config default)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        from_email = from_email or self.default_from_email
        from_name = from_name or self.default_from_name
        from_header = f"{from_name} <{from_email}>"
        
        data = {
            "from": from_header,
            "to": to,
            "subject": subject,
            "text": text,
            "html": html
        }
        
        try:
            response = requests.post(
                self.base_url,
                auth=("api", self.api_key),
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Email sent successfully to {to} via Mailgun")
                return True
            else:
                logger.error(
                    f"Failed to send email via Mailgun: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            logger.error(f"Exception sending email via Mailgun: {e}")
            return False
    
    def get_provider_name(self) -> str:
        """
        Get the name of this provider.
        
        Returns:
            str: Provider name
        """
        return "mailgun"

