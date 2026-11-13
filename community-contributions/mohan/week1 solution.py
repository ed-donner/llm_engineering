"""
Day 2 exercise: the Day 1 website summarizer, upgraded to use an open-source
model running locally via Ollama instead of OpenAI.

Usage (from the week1 directory):
    uv run solution.py https://edwarddonner.com
    uv run solution.py https://anthropic.com --model llama3.2:1b
    uv run solution.py            # prompts for a URL
"""

import argparse
import sys

import requests
from openai import OpenAI

from scraper import fetch_website_contents

OLLAMA_URL = "http://localhost:11434"
OLLAMA_BASE_URL = f"{OLLAMA_URL}/v1"
DEFAULT_MODEL = "llama3.2"

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
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_prefix + website},
    ]


def check_ollama():
    """Exit with a helpful message if the Ollama server isn't running."""
    try:
        requests.get(OLLAMA_URL, timeout=5)
    except requests.exceptions.ConnectionError:
        sys.exit(f"Ollama isn't running at {OLLAMA_URL} - start it with `ollama serve`")


def summarize(url, model=DEFAULT_MODEL):
    # Ollama exposes an OpenAI-compatible endpoint; the api_key is required by the client but ignored
    ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    website = fetch_website_contents(url)
    response = ollama.chat.completions.create(model=model, messages=messages_for(website))
    return response.choices[0].message.content


def main():
    # Windows consoles default to cp1252, which can't print the emoji LLMs love
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Summarize a website using a local Ollama model")
    parser.add_argument("url", nargs="?", help="URL of the website to summarize")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model to use (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    url = args.url or input("Enter a URL to summarize: ").strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    check_ollama()
    print(f"\nSummarizing {url} with {args.model}...\n")
    print(summarize(url, args.model))


if __name__ == "__main__":
    main()
