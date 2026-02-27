from openai import OpenAI

from week1.scraper import fetch_website_contents

deep_seek = OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="deepseek")

website_contents = fetch_website_contents(
    "https://www.coinbase.com/learn/crypto-basics"
)

system_prompt = "You are a helpful crypto tutor. You are an expert in crypto and blockchain. You are able to answer questions about crypto and blockchain."
user_prompt = f"""
    Make a short summary of the following website:
    {website_contents}
"""

# Step 2: Make the messages list

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt},
]

# Step 3: Call OpenAI
response = deep_seek.chat.completions.create(
    model="deepseek-r1:1.5b", messages=messages
)

# Step 4: print the result
print(response.choices[0].message.content)
