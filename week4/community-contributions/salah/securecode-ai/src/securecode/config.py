"""Configuration management for SecureCode AI."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # API Configuration
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    # Model Configuration
    DEFAULT_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
    MODEL = os.getenv("SECURECODE_MODEL", DEFAULT_MODEL)

    # Application Settings
    APP_NAME = "SecureCode AI"
    APP_DESCRIPTION = "AI-powered code security and performance analyzer"

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY not found. "
                "Please set it in .env file or environment variables."
            )

    @classmethod
    def get_model_display_name(cls):
        """Get a user-friendly model name."""
        return cls.MODEL.split("/")[-1].replace("-", " ").title()
