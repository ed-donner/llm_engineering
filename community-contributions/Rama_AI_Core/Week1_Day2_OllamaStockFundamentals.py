import os
from dotenv import load_dotenv
from IPython.display import Markdown, display
from openai import OpenAI

# Core step : Set the API key
load_dotenv(override=True)

# Step 1: Create your prompts

system_prompt = "You are a helpful assistant that can help me with my stock fundamentals analysis."
user_prompt = """
    Give me the fundamentals of the stock AMZN. This includes the P/E ratio, EPS, ROE, and other relevant metrics.
    Give the results as numerical values without your commentary. Give the result as JSON format.
"""

# Step 2: Make the messages list

messages = [
    {"role" : "system", "content" : system_prompt},
    {"role" : "user", "content" : user_prompt}
] # fill this in

# Step 3: Call OpenAI
OLLAMA_BASE_URL = "http://localhost:11434/v1"

ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key='ollama')

response = ollama.chat.completions.create(model="llama3.2", messages=messages)

# Step 4: print the result
print(response.choices[0].message.content)

