"""
Application configuration and settings.

Manages environment variables, default values, and logging configuration.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings with environment variable support."""

    # API Keys (loaded from .env or provided by user)
    HUGGINGFACE_API_KEY: Optional[str] = os.getenv("HUGGINGFACE_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///synth_data.db")

    # Generation Defaults
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 2048
    MAX_RETRIES: int = 3

    # UI
    APP_TITLE: str = "Synthetic Data Generator v2"
    PAGE_ICON: str = "🎲"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "synth_data.log")


# Singleton instance
settings = Settings()


def configure_logging(level: Optional[str] = None) -> None:
    """
    Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = level or settings.LOG_LEVEL

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.LOG_FILE),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {log_level} level")
