import os
import urllib.request
from dotenv import load_dotenv
from openai import OpenAI
import tempfile
from ddgs import DDGS

load_dotenv(override=True)

OPENROUTER_URL = "https://openrouter.ai/api/v1"
OLLAMA_BASE_URL = "http://localhost:11434/v1"

system_message = """
You are a helpful assistant that can answer questions and help with tasks.
"""

MODELS = {
    "GPT": "gpt-4o-mini",
    "Claude": "anthropic/claude-sonnet-4",
    "Gemini": "google/gemini-2.0-flash-exp:free",
    "Llama": "llama3.2",
}

openrouter = OpenAI(
    base_url=OPENROUTER_URL,
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def ollama_is_running():
    try:
        with urllib.request.urlopen(f"http://localhost:11434/api/tags", timeout=2) as r:
            return r.status == 200
    except OSError:
        return False

ollama = (
    OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    if ollama_is_running()
    else None
)

def get_client_and_model(model_choice):
    if model_choice == "Llama":
        if ollama is None:
            raise RuntimeError("Ollama is not running. Start it with: ollama serve")
        return ollama, MODELS["Llama"]
    return openrouter, MODELS[model_choice]


def generate_tts(text):
    if not text.strip():
        return None
    openai_direct = OpenAI()
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            response = openai_direct.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text[:4096],  # TTS has a 4096 char limit
            )
            response.stream_to_file(f.name)
            return f.name
    except Exception as e:
        print(f"TTS error: {e}")
        return None

def get_system_prompt():
    PROMPT_FILE = "system_prompt.txt"
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            SYSTEM_PROMPT = f.read().strip()
    except FileNotFoundError:
        SYSTEM_PROMPT = "You are a helpful assistant that can answer questions about technical topics."

    return SYSTEM_PROMPT

def search_web(query: str, num_results: int = 3) -> dict:
    print("searching web with query: ", query)
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=num_results):
            results.append({
                "title": r["title"],
                "url": r["href"],
                "snippet": r["body"]
            })
    return {"query": query, "results": results}