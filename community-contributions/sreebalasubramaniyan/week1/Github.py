import os
from dotenv import load_dotenv
from openai import OpenAI

# Github summerizer by it's readme file

load_dotenv()

OPEN_ROUTER_URL = "https://openrouter.ai/api/v1"
api_key = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url=OPEN_ROUTER_URL,
    api_key=api_key
)
def chat(prompt):
    try:
        response = client.chat.completions.create(
        model="cohere/north-mini-code:free",
            messages=[{"role": "user", "content": prompt}]
        )

        res = (response.choices[0].message.content)

    except Exception as e:
        res = ("Error:", e)

    return res

prompt = """You are a senior software engineer.

Analyze this GitHub repository README and provide:

1. Summary
2. Main Features
3. Tech Stack
4. Difficulty Level
5. Learning Prerequisites
6. Architecture Overview
7. Resume Value
8. 10 Interview Questions

README:
"""

# scrapping the readme
import requests

url = "https://raw.githubusercontent.com/ed-donner/llm_engineering/master/README.md"

readme = requests.get(url).text


prompt += readme

res = chat(prompt)

print(res)