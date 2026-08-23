import os
from dotenv import load_dotenv
from litellm import completion

load_dotenv(override=True)

API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError("OPENROUTER_API_KEY is not set in .env")

MODEL = os.getenv("MODEL", "openai/gpt-4.1-nano")

SYSTEM_PROMPT = """
You are a senior database engineer.
Convert SQL queries to MongoDB queries.
Return only the MongoDB query.
"""

def convert_sql_to_mongo(sql_query: str):

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": sql_query}
    ]

    response = completion(
        model=MODEL,
        messages=messages,
        api_key=API_KEY,
        api_base="https://openrouter.ai/api/v1",
        temperature=0
    )

    return response.choices[0].message.content