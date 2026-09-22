import openai  # type: ignore
import ollama  # type: ignore
from utils.config import Config
import requests # type: ignore


# Initialize clients
openai_client = openai.Client(api_key=Config.OPENAI_API_KEY)
ollama_api_url = Config.OLLAMA_API_URL

def call_llm(messages, model="gpt-4", provider="openai"):
    """
    Generic function to call the appropriate LLM provider.
    Supports: openai, deepseek, llama.
    """
    if provider == "openai":
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content

    elif provider == "ollama_lib":
        response = ollama.chat(
            model=model,
            messages=messages
        )
        return response['message']['content']

    elif provider == "ollama_api":
        payload = {
            "model": model,
            "messages": messages,
            "stream": False  # Set to True for streaming responses
        }
        response = requests.post(ollama_api_url, json=payload)
        response_data = response.json()
        return response_data.get('message', {}).get('content', 'No summary generated')

    else:
        raise ValueError("Unsupported provider. Choose 'openai', 'deepseek', or 'llama'.")