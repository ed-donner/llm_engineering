"""
Week 1 Day 2 – Homework solution: summarize a webpage using Ollama (local open-source model).

Upgrades the Day 1 project to use an open-source model running locally via Ollama instead of OpenAI.
Run: uv run wk1_day2_solution.py [URL]
     or from repo root: uv run week1/wk1_day2_solution.py [URL]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure week1 is on path when run as script from repo root (e.g. uv run week1/wk1_day2_solution.py)
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from openai import OpenAI

from scraper import fetch_website_contents


# Ollama runs locally; no API key needed. Use a placeholder for the OpenAI-compatible client.
OLLAMA_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3.2"  # Use "llama3.2:1b" if Ollama is slow on your machine

# Prompts (aligned with Day 1)
SYSTEM_PROMPT = """
You are a snarky assistant that analyzes the contents of a website,
and provides a short, snarky, humorous summary, ignoring text that might be navigation related.
Respond in markdown. Do not wrap the markdown in a code block - respond just with the markdown.
"""

USER_PROMPT_PREFIX = """
Here are the contents of a website.
Provide a short summary of this website.
If it includes news or announcements, then summarize these too.

"""


def messages_for(website: str) -> list[dict[str, str]]:
    """Build the messages list for the chat API (system + user with website content)."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_PREFIX + website},
    ]


def summarize(
    url: str,
    *,
    client: OpenAI | None = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Fetch the webpage at `url`, send its contents to Ollama, and return the summary text.
    Requires Ollama to be running locally (e.g. ollama serve, ollama pull llama3.2).
    """
    if client is None:
        client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    website = fetch_website_contents(url)
    response = client.chat.completions.create(
        model=model,
        messages=messages_for(website),
    )
    return (response.choices[0].message.content or "").strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize a webpage using a local Ollama model (Week 1 Day 2 solution)."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default="https://edwarddonner.com",
        help="URL to summarize (default: https://edwarddonner.com)",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=DEFAULT_MODEL,
        help=f"Ollama model name (default: {DEFAULT_MODEL}; use llama3.2:1b if slow)",
    )
    args = parser.parse_args()

    try:
        client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
        summary = summarize(args.url, client=client, model=args.model)
        print(summary)
        return 0
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        print(
            "Ensure Ollama is running: visit http://localhost:11434/ or run 'ollama serve' and 'ollama pull llama3.2'.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
