import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model Selection
DEFAULT_MODEL = "google/gemini-2.0-flash-001"

# Available models for the UI dropdowns
AVAILABLE_MODELS = [
    "google/gemini-2.0-flash-001",
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4o-mini",
    "openai/gpt-4o",
    "meta-llama/llama-4-scout",
    "deepseek/deepseek-chat-v3-0324",
]

# Tool Configurations
SERP_API_KEY = os.getenv("SERP_API_KEY")

from langchain_openai import ChatOpenAI

def get_llm(model_name=DEFAULT_MODEL, temperature=0):
    """Returns a ChatOpenAI instance configured for OpenRouter."""
    return ChatOpenAI(
        model=model_name,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        temperature=temperature,
        default_headers={
            "X-Title": "Multi-Agent Research Assistant",
        }
    )
