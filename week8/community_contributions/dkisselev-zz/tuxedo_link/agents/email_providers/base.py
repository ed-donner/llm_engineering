"""Base email provider interface."""

from abc import ABC, abstractmethod
from typing import Dict, Optional


class EmailProvider(ABC):
    """Abstract base class for email providers."""
    
    @abstractmethod
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
        Send an email.
        
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
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of this provider.
        
        Returns:
            str: Provider name
        """
        pass

