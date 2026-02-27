import os

from dotenv import load_dotenv
from openai import OpenAI

from week1.scraper import fetch_website_contents

load_dotenv(override=True)
api_key = os.getenv("OPENAI_API_KEY")

openai = OpenAI(api_key=api_key)
website_contents = fetch_website_contents(
    "https://www.coinbase.com/learn/crypto-basics"
)

system_prompt = "You are a helpful crypto tutor. You are an expert in crypto and blockchain. You are able to answer questions about crypto and blockchain."
user_prompt = """
    Make a short summary of the following website:
    {website_contents}
"""

# Step 2: Make the messages list

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt},
]

# Step 3: Call OpenAI
response = openai.chat.completions.create(model="gpt-4.1-nano", messages=messages)

# Step 4: print the result
print(response.choices[0].message.content)
