"""Email provider factory."""

import os
import logging
from typing import Optional
from .base import EmailProvider
from .mailgun_provider import MailgunProvider
from .sendgrid_provider import SendGridProvider
from utils.config import get_email_provider as get_configured_provider


logger = logging.getLogger(__name__)


def get_email_provider(provider_name: Optional[str] = None) -> EmailProvider:
    """
    Get an email provider instance.
    
    Args:
        provider_name: Provider name (mailgun or sendgrid).
                      If None, uses configuration from config.yaml
    
    Returns:
        EmailProvider: Configured email provider instance
        
    Raises:
        ValueError: If provider name is unknown
    """
    if not provider_name:
        provider_name = get_configured_provider()
    
    provider_name = provider_name.lower()
    
    logger.info(f"Initializing email provider: {provider_name}")
    
    if provider_name == 'mailgun':
        return MailgunProvider()
    elif provider_name == 'sendgrid':
        return SendGridProvider()
    else:
        raise ValueError(
            f"Unknown email provider: {provider_name}. "
            "Valid options are: mailgun, sendgrid"
        )

