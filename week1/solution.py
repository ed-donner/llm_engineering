"""
Website summarizer using a local Ollama model instead of OpenAI.

Usage:
    uv run python week1/solution.py <url>
    uv run python week1/solution.py  (defaults to https://edwarddonner.com)
"""

import sys
import os

# Allow imports from the week1 directory when run from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openai import OpenAI
from scraper import fetch_website_contents

OLLAMA_BASE_URL = "http://localhost:11434/v1"
MODEL = "llama3.2"

system_prompt = """
You are a snarky assistant that analyzes the contents of a website,
and provides a short, snarky, humorous summary, ignoring text that might be navigation related.
Respond in markdown. Do not wrap the markdown in a code block - respond just with the markdown.
"""

user_prompt_prefix = """
Here are the contents of a website.
Provide a short summary of this website.
If it includes news or announcements, then summarize these too.

"""


def messages_for(website):
    """Create message list for the LLM."""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_prefix + website},
    ]


def summarize(url):
    """Fetch and summarize a website using Ollama."""
    ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    website = fetch_website_contents(url)
    response = ollama.chat.completions.create(
        model=MODEL,
        messages=messages_for(website),
    )
    return response.choices[0].message.content


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://edwarddonner.com"
    print(f"Summarizing {url} with {MODEL} via Ollama...\n")
    summary = summarize(url)
    print(summary)


if __name__ == "__main__":
    main()
