# Get a fun fact

# response = ollama.chat.completions.create(model="gemma4:E4B", messages=[{"role": "user", "content": "Tell me a fun fact"}])
# response.choices[0].message.content

# imports
# activate venv

import os
from dotenv import load_dotenv
#from scraper import fetch_website_contents
from IPython.display import Markdown, display
from openai import OpenAI

# Define our system prompt - you can experiment with this later, changing the last sentence to 'Respond in markdown in Spanish."

system_prompt = """
You are a professional assistant that analyzes the contents of a website,
and provides a short summary of features, ignoring text that might be navigation related.
Respond in markdown. Do not wrap the markdown in a code block - respond just with the markdown.
"""

# Define our user prompt

user_prompt_prefix = """
Parse the website and provide a short feature summary. Ignore text that might be navigation related. Here is the website: 

"""
# See how this function creates exactly the format above

def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_prefix + website}
    ]

# And now: call the OpenAI API. You will get very familiar with this!

def summarize(url):
    #website = fetch_website_contents(url)
    # Load environment variables in a file called .env
    load_dotenv(override=True)
    model_url = os.getenv('OLLAMA_BASE_URL')

    ollama = OpenAI(base_url=model_url, api_key='ollama')
    response = ollama.chat.completions.create(
        model = "gemma4:E4B",
        messages = messages_for(url)
    )
    return response.choices[0].message.content

# A function to display this nicely in the output, using markdown

def display_summary(url):
    summary = summarize(url)
    display(Markdown(summary))
    print(summary)

display_summary("https://www.google.com")

