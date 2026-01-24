import os
from dotenv import load_dotenv
from IPython.display import Markdown, display
from openai import OpenAI

# Core step : Set the API key
load_dotenv(override=True)

# Step 1: Create your prompts

system_prompt = "You are a helpful assistant that can help me with my stock fundamentals analysis."
user_prompt = """
    Give me the summary of ER report of stock AMZN whatever recent quarter you have access to. 
    Give top 5 positive and top 5 negative points based on ER transcript with analysts.
    It need not be the most recent ER report, but the most recent one you have access to.
"""

# Step 2: Make the messages list

messages = [
    {"role" : "system", "content" : system_prompt},
    {"role" : "user", "content" : user_prompt}
] # fill this in

# Step 3: Call OpenAI
openai = OpenAI()
response = openai.chat.completions.create(model="gpt-5.2", messages=messages)

# Step 4: print the result
print(response.choices[0].message.content)

