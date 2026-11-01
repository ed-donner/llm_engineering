# maybe enchaced webscraper that uses local ai model to tell about vulnerabilites in the hosted website

import os
from dotenv import load_dotenv
from openai import OpenAI
import requests

load_dotenv(override=True)

base_url = "http://localhost:11434/v1"
api_key = "ollama"

client = OpenAI(
    base_url=base_url,
    api_key=api_key
)

def get_data_from_url(url: str):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        if "application/json" in response.headers.get("Content-Type", ""):
            return response.json()

        return response.text

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


data = get_data_from_url("https://hashimalzuraiqi.me/")

messages = [
    {
        "role": "system",
        "content": "You are a web analyzer and scraper. Analyze website content carefully."
    },
    {
        "role": "user",
        "content": f"""
Analyze this website content and summarize:

1. Possible security vulnerabilities or exposed information.
2. Any suspicious claims or indicators that the person might be exaggerating or lying.
3. Give the answer in simple clear points.

Website content:

{data}
"""
    }
]

response = client.chat.completions.create(
    model="llama3.2",
    messages=messages
)

print(response.choices[0].message.content)