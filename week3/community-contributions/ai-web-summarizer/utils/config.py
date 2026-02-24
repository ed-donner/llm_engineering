import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if __name__ == "__main__":
    print("Your OpenAI Key is:", Config.OPENROUTER_API_KEY)