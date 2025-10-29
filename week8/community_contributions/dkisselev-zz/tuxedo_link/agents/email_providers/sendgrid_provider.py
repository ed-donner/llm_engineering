"""SendGrid email provider implementation (stub)."""

import os
import logging
from typing import Optional
from .base import EmailProvider
from utils.config import get_email_config


logger = logging.getLogger(__name__)


class SendGridProvider(EmailProvider):
    """SendGrid email provider (stub implementation)."""
    
    def __init__(self):
        """Initialize SendGrid provider."""
        self.api_key = os.getenv('SENDGRID_API_KEY')
        
        email_config = get_email_config()
        self.default_from_name = email_config['from_name']
        self.default_from_email = email_config['from_email']
        
        logger.info("SendGrid provider initialized (stub mode)")
        if not self.api_key:
            logger.warning("SENDGRID_API_KEY not set - stub will only log, not send")
    
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
        Send an email via SendGrid (stub - only logs, doesn't actually send).
        
        Args:
            to: Recipient email address
            subject: Email subject
            html: HTML body
            text: Plain text body
            from_email: Sender email (optional, uses config default)
            from_name: Sender name (optional, uses config default)
            
        Returns:
            bool: True (always succeeds in stub mode)
        """
        from_email = from_email or self.default_from_email
        from_name = from_name or self.default_from_name
        
        logger.info(f"[STUB] Would send email via SendGrid:")
        logger.info(f"  From: {from_name} <{from_email}>")
        logger.info(f"  To: {to}")
        logger.info(f"  Subject: {subject}")
        logger.info(f"  Text length: {len(text)} chars")
        logger.info(f"  HTML length: {len(html)} chars")
        
        # Simulate success
        return True
    
    def get_provider_name(self) -> str:
        """
        Get the name of this provider.
        
        Returns:
            str: Provider name
        """
        return "sendgrid (stub)"

