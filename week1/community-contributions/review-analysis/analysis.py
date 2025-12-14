from data import get_comments

import os
from dotenv import load_dotenv
from openai import OpenAI

from rich.console import Console
from rich.markdown import Markdown

load_dotenv(override=True)

DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

def print_markdown(content):
    """Show markdown formatted text in the console."""
    console = Console()
    markdown = Markdown(content)
    console.print(markdown)

def comments_to_text():
    """Convert the list of comments into a single formatted text."""
    comments = get_comments()
    return "\n".join([f"{i+1}. {comment.strip()}" for i, comment in enumerate(comments)])

def get_system_prompt():
    """Return the system prompt"""
    with open("week1/community-contributions/review-analysis/system_prompt.txt", "r") as file:
        return file.read()

def get_user_prompt():
    """Return the user prompt"""
    with open("week1/community-contributions/review-analysis/user_prompt.txt", "r") as file:
        return file.read()

comments = comments_to_text()

system_prompt = get_system_prompt()
user_prompt = get_user_prompt() + comments

def messages(system_prompt=system_prompt, user_prompt=user_prompt):
    """Create the message structure for the chat API."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    return messages

def summarize_comments():
    """Generate a summary of the comments using the Deepseek API."""

    # Configure the Deepseek API
    deepseek = OpenAI(api_key=deepseek_api_key, base_url=DEEPSEEK_BASE_URL)

    # Call the chat API with the prepared messages
    response = deepseek.chat.completions.create(
        model="deepseek-chat",
        messages=messages()

    )

    # Extract the content from the response
    content = response.choices[0].message.content

    # Display the content formatted in Markdown
    print_markdown(content)

summarize_comments()