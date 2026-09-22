import openai  # type: ignore
import ollama
import requests
from utils.config import Config

# Local Ollama API endpoint
OLLAMA_API = "http://127.0.0.1:11434/api/chat"

# Initialize OpenAI client with API key
client = openai.Client(api_key=Config.OPENAI_API_KEY)

def summarize_with_openai(text, model):
    """Summarize text using OpenAI's GPT model."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes web pages."},
                {"role": "user", "content": f"Summarize the following text: {text}"}
            ],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error during OpenAI summarization: {e}")
        return None

def summarize_with_ollama_lib(text, model):
    """Summarize text using Ollama Python library."""
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant that summarizes web pages."},
            {"role": "user", "content": f"Summarize the following text: {text}"}
        ]
        response = ollama.chat(model=model, messages=messages)
        return response['message']['content']
    except Exception as e:
        print(f"Error during Ollama summarization: {e}")
        return None

def summarize_with_ollama_api(text, model):
    """Summarize text using local Ollama API."""
    try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that summarizes web pages."},
                {"role": "user", "content": f"Summarize the following text: {text}"}
            ],
            "stream": False  # Set to True for streaming responses
        }
        response = requests.post(OLLAMA_API, json=payload)
        response_data = response.json()
        return response_data.get('message', {}).get('content', 'No summary generated')
    except Exception as e:
        print(f"Error during Ollama API summarization: {e}")
        return None

def summarize_text(text, model, engine="openai"):
    """Generic function to summarize text using the specified engine (openai/ollama-lib/ollama-api)."""
    if engine == "openai":
        return summarize_with_openai(text, model)
    elif engine == "ollama-lib":
        return summarize_with_ollama_lib(text, model)
    elif engine == "ollama-api":
        return summarize_with_ollama_api(text, model)
    else:
        print("Invalid engine specified. Use 'openai', 'ollama-lib', or 'ollama-api'.")
        return None

if __name__ == "__main__":
    sample_text = "Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to the natural intelligence displayed by animals and humans."

    # Summarize using OpenAI
    openai_summary = summarize_text(sample_text, model="gpt-3.5-turbo", engine="openai")
    print("OpenAI Summary:", openai_summary)

    # Summarize using Ollama Python library
    ollama_lib_summary = summarize_text(sample_text, model="deepseek-r1:1.5B", engine="ollama-lib")
    print("Ollama Library Summary:", ollama_lib_summary)

    # Summarize using local Ollama API
    ollama_api_summary = summarize_text(sample_text, model="deepseek-r1:1.5B", engine="ollama-api")
    print("Ollama API Summary:", ollama_api_summary)
