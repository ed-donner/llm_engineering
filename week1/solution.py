"""Day 2 challenge solution: summarize webpages using local Ollama."""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI
from scraper import fetch_website_contents

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"

SYSTEM_PROMPT = (
    "You are a concise assistant that summarizes website content. "
    "Ignore navigation and boilerplate where possible. "
    "Return clear markdown with key points."
)

USER_PROMPT_PREFIX = """
Here are the contents of a website.
Provide a short summary of this website.
If it includes news or announcements, then summarize these too.

"""


def messages_for(website_text: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_PREFIX + website_text},
    ]


def summarize(url: str, model: str, base_url: str) -> str:
    website = fetch_website_contents(url)
    client = OpenAI(base_url=base_url, api_key="ollama")
    response = client.chat.completions.create(
        model=model,
        messages=messages_for(website),
    )
    return response.choices[0].message.content or ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize a webpage using a local Ollama model."
    )
    parser.add_argument("url", help="URL to summarize")
    parser.add_argument(
        "--model",
        default=os.getenv("OLLAMA_MODEL", "mistral-small3.2:latest"),
        help=f'Ollama model name (default: "mistral-small3.2:latest")',
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
        help=f'Ollama OpenAI-compatible base URL (default: "{DEFAULT_OLLAMA_BASE_URL}")',
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv(override=False)
    args = parse_args()

    try:
        summary = summarize(args.url, model=args.model, base_url=args.base_url)
    except Exception as exc:  # pragma: no cover - friendly CLI error
        print(f"Error while summarizing {args.url}: {exc}", file=sys.stderr)
        return 1

    print(summary.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""
Website summarizer using Ollama instead of OpenAI.
"""

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
        {"role": "user", "content": user_prompt_prefix + website}
    ]


def summarize(url):
    """Fetch and summarize a website using Ollama."""
    ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key='ollama')
    website = fetch_website_contents(url)
    response = ollama.chat.completions.create(
        model=MODEL,
        messages=messages_for(website)
    )
    return response.choices[0].message.content


def main():
    """Main entry point for testing."""
    url = input("Enter a URL to summarize: ")
    print("\nFetching and summarizing...\n")
    summary = summarize(url)
    print(summary)


if __name__ == "__main__":
    main()
