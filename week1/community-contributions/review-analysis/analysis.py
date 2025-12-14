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

comments = comments_to_text()

system_prompt = """
You are an assistant specialized in comment analysis. Your task is to carefully analyze the texts of the provided comments and identify important information and syntheses for a final feedback. Consider the general tone, context, intensity of opinions, and possible ambiguities.
"""
user_prompt = f"""
Based on the product review comments below, make a table with 7 rows and 2 columns called Analysis, Result.

Row 1: Summary
a very short summary of the analysis of the comments, highlighting the most relevant points mentioned by users.

Row 2: Sentiment Analysis
a sentiment analysis in each one. Classify the sentiment as positive, negative or neutral. The response should contain a very short and simple general summary of the analysis performed.

Row 3: Most positive review
Indicate the most positive comment, without considerations.

Row 4: Most negative review
Indicate the most negative comment, without considerations.

Row 5: Final Feedback
A short final feedback from the analysis of the comments.

Row 6: Categories (hashtags)
Identify the topics mentioned in the comments and group them into categories, providing only the category name to summarize all comments.

Row 7: Analysis Score
Provide an overall rating from 0 to 5 stars based on the analysis of the comments.

Comments:

{comments}".

Note: It is not necessary to mention individual comments in the analysis.
"""

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