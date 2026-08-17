from openai import OpenAI
import os

def get_client(provider="openai"):

    configs = {
        "openai": {
            "client": OpenAI(
                api_key=os.getenv("OPENAI_API_KEY")
            )
        },

        "ollama": {
            "client": OpenAI(
                base_url="https://ollama.com/v1",
                api_key=os.getenv("OLLAMA_API_KEY")
            )
        }
    }

    return configs[provider]


def get_models():
    MODELS = {
        "cheap": "gpt-oss:20b",
        "medium": "gemma4:31b",
        "large": "qwen3.5:397b"
    }

    return MODELS