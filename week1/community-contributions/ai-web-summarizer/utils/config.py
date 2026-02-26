import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if __name__ == "__main__":
    print("Your OpenAI Key is:", Config.OPENAI_API_KEY)