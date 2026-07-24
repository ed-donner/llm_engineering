"""
Day 1 Exercises using Claude (Anthropic API):
- Example 1: Email subject line generator
- Example 2: Website Summarizer using a Selenium scraper (for JS-rendered sites)

This is a Claude-based adaptation of the course's day1.ipynb exercise.

Folder structure:
    community-contributions/rizwan_rumi/week1/python/day1_with_claude.py
    community-contributions/rizwan_rumi/week1/python/scraper_selenium.py
"""

import os
from dotenv import load_dotenv
from anthropic import Anthropic

from scraper_selenium import fetch_website_contents_selenium

# Load API key and set up the Claude client

load_dotenv(override=True)
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key or not api_key.startswith("sk-ant-"):
    raise ValueError(
        "No valid ANTHROPIC_API_KEY found. "
        "Please add ANTHROPIC_API_KEY=sk-ant-... to .env file."
    )

claude = Anthropic()

# -------------------------------
# Example 1: Email subject line generator
# -------------------------------

system_prompt_ex1 = """
You are a very sincere assistant that reads the contents of an email 
and suggests a short, clear, professional subject line for it.
Respond with only the subject line, nothing else.
"""

user_prompt_ex1 = """
Hi team,

Just a heads up that the weekly SWD meeting originally scheduled for Thursday
at 2pm has been moved to Wednesday at 9:15am due to a scheduling conflict on
manager end. Please update your calendars accordingly. Let me know if this
new time doesn't work for anyone and we'll try to find an alternative.

Thanks,
Rizwan
"""

def suggest_subject_line_claude(email_text):
    response = claude.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=100,
        system=system_prompt_ex1,
        messages=[{"role": "user", "content": email_text}],
    )
    return response.content[0].text


# -------------------------------
# Example 2: Website summarizer for JavaScript-rendered sites (Selenium)
# -------------------------------

system_prompt_ex2 = (
    "You are an assistant that analyzes the contents of a website "
    "and provides a short, informative summary, ignoring text that "
    "might be navigation-related."
)

user_prompt_prefix_ex2 = (
    "You are looking at a website. "
    "The contents of this website are as follows; "
    "please provide a short summary of this website in markdown. "
    "If it includes news or announcements, summarize these too.\n\n"
)

def summarize_js_site(url):
    website_text = fetch_website_contents_selenium(url)

    response = claude.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=system_prompt_ex2,
        messages=[{"role": "user", "content": user_prompt_prefix_ex2 + website_text}],
    )
    return response.content[0].text


def display_summary(url):
    summary = summarize_js_site(url)
    print(f"\n{'=' * 80}\nSummary for {url}\n{'=' * 80}\n")
    print(summary)



# Run examples

if __name__ == "__main__":
    # Example 1
    print(suggest_subject_line_claude(user_prompt_ex1))

    # Example 2
    display_summary("https://openai.com")