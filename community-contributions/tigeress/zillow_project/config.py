# ─────────────────────────────────────────
# config.py
# ─────────────────────────────────────────
import os
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

# Load .env file automatically
load_dotenv(find_dotenv(), override=True)

# Constants
MODEL_GPT      = 'gpt-4o-mini'
RAPIDAPI_HOST  = "unofficial-zillow-api2.p.rapidapi.com"
RAPIDAPI_KEY   = os.getenv("RAPIDAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# RapidAPI Headers
HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": RAPIDAPI_HOST,
    "x-rapidapi-key": RAPIDAPI_KEY
}

# Verify keys loaded
print("✅ OpenAI Key loaded!"   if OPENAI_API_KEY else "❌ OpenAI Key missing!")
print("✅ RapidAPI Key loaded!" if RAPIDAPI_KEY   else "❌ RapidAPI Key missing!")