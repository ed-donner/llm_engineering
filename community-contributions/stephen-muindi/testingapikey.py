# Sample code to test API Key from OpenRouter.ai

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

print("DEBUG: API KEY == ", os.getenv("OPENROUTER_API_KEY"))

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

response = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}],
)

print(response.choices[0].message.content)