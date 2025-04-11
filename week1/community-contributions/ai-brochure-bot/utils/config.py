import os
from dotenv import load_dotenv # type: ignore

# Load environment variables from .env file
load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")

if __name__ == "__main__":
    print("OpenAI Key is:", Config.OPENAI_API_KEY)
    print("Ollama Api Url is:", Config.OLLAMA_API_URL)