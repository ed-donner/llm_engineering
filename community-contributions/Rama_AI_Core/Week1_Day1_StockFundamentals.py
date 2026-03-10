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
openai = OpenAI()
response = openai.chat.completions.create(model="gpt-4.1-mini", messages=messages)

# Step 4: print the result
print(response.choices[0].message.content)

