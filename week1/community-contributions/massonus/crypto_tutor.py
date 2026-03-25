from openai import OpenAI

from week1.scraper import fetch_website_contents

deep_seek = OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="deepseek")

website_contents = fetch_website_contents(
    "https://www.coinbase.com/learn/crypto-basics"
)

system_prompt = "Ты эксперт в области криптовалют и блокчейна. Ты можешь ответить на вопросы по этой теме. И отвечаешь на русском языке."
user_prompt = f"""
    Создай краткое изложение следующего сайта:
    {website_contents}
"""

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
