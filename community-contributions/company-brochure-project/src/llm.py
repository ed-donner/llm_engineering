"""
llm.py
------

Responsible only for setting up the LLM client used throughout the
project: loading environment variables and initializing the
OpenAI-compatible client pointed at a local Ollama server.

No prompts, scraping, or brochure-generation logic lives here.
"""

from __future__ import annotations

from dotenv import load_dotenv
from openai import OpenAI

# ==========================
# Environment
# ==========================

# Load environment variables from a .env file, if present. Kept for parity
# with the original notebook (e.g. in case OPENAI_API_KEY or other
# environment-based configuration is needed later).
load_dotenv(override=True)

# ==========================
# Model / Client configuration
# ==========================

# ==========================
# OpenAI Version (Paid API) - kept for reference, not used by default
# ==========================
#
# api_key = os.getenv('OPENAI_API_KEY')
#
# if api_key and api_key.startswith('sk-proj-') and len(api_key) > 10:
#     print("API key looks good so far")
# else:
#     print("There might be a problem with your API key? Please visit the troubleshooting notebook!")
#
# MODEL = 'gpt-5-nano'
# openai_client = OpenAI()

# ==========================
# Ollama Version (Free / Local) - active configuration
# ==========================

MODEL: str = "llama3.2"

OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
OLLAMA_API_KEY: str = "ollama"

# OpenAI-compatible client pointed at the local Ollama server.
ollama_client: OpenAI = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key=OLLAMA_API_KEY,
)


def get_client() -> OpenAI:
    """
    Return the initialized OpenAI-compatible client used to talk to the
    local Ollama server.

    :return: The configured OpenAI client instance.
    """
    return ollama_client
