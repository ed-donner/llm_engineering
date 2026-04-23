from openai import OpenAI
from config import OLLAMA_BASE_URL, MODEL_NAME


def create_client() -> OpenAI:
    """
    Create and return an OpenAI-compatible client pointed at Ollama.

    Returns:
        OpenAI: Configured client instance.
    """
    return OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")


def get_response(messages: list, client: OpenAI) -> str:
    """
    Send the current conversation history to the LLM and return its response.

    Args:
        messages (list): The full conversation history so far.
        client (OpenAI): The OpenAI client instance.

    Returns:
        str: The LLM's response text.
    """
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages
    )
    return response.choices[0].message.content
