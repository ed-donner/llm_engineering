# Solution: Upgrade Day 1 project to use Ollama instead of OpenAI

# Import necessary modules
from scraper import fetch_website_contents
from IPython.display import Markdown, display
from openai import OpenAI

# Set up Ollama client (using the OpenAI compatible endpoint)
# Note: Make sure Ollama is running (ollama serve) and you've pulled a model (ollama pull llama3.2)
OLLAMA_BASE_URL = "http://localhost:11434/v1"
ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key='ollama')

# Define the model - you can change this to llama3.2:1b if your machine is slower
MODEL = "llama3.2:1b"  # or "llama3.2:1b" for smaller machines

# Define system prompt (same as Day 1)
system_prompt = """
You are a helpful assistant that analyzes the contents of a website,
and provides a short summary, ignoring text that might be navigation related.
Respond in markdown. Do not wrap the markdown in a code block - respond just with the markdown.
"""

# Define user prompt prefix (same as Day 1)
user_prompt_prefix = """
Here are the contents of a website.
Provide a short summary of this website.
If it includes news or announcements, then summarize these too.

"""

# Function to create messages (same as Day 1)
def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_prefix + website}
    ]

# Summarize function using Ollama instead of OpenAI
def summarize(url):
    website = fetch_website_contents(url)
    response = ollama.chat.completions.create(
        model=MODEL,
        messages=messages_for(website)
    )
    return response.choices[0].message.content

# Function to display summary nicely in markdown
def display_summary(url):
    summary = summarize(url)
    display(Markdown(summary))

