import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

MODELS = {
    "gpt-4.1-mini": {
        "provider": "openai",
        "model_name": "gpt-4.1-mini",
    },
    "groq/openai/gpt-oss-120b": {
        "provider": "groq",
        "model_name": "openai/gpt-oss-120b",
    },
    "llama3.2": {
        "provider": "ollama",
        "model_name": "llama3.2",
    },
}


def _build_clients() -> dict[str, OpenAI]:
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    groq_client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
    )
    ollama_client = OpenAI(
        api_key="ollama",
        base_url="http://localhost:11434/v1",
    )
    return {
        "openai": openai_client,
        "groq": groq_client,
        "ollama": ollama_client,
    }


_clients: dict[str, OpenAI] | None = None


def get_client(model_key: str) -> tuple[OpenAI, str, str]:
    """Return (client, api_model_name, provider) for a given model key."""
    global _clients
    if _clients is None:
        _clients = _build_clients()

    info = MODELS[model_key]
    provider = info["provider"]
    return _clients[provider], info["model_name"], provider