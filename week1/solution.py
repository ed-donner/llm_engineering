
import os
from dotenv import load_dotenv
from scraper import fetch_website_contents
from IPython.display import Markdown, display
from openai import OpenAI

# Load environment variables from .env file
load_dotenv(override=True)

# Recommended: Define constants for your model and base URL
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "llama3.2"  # Or "llama3.2:1b" if you have a smaller machine

# Initialize the OpenAI client to connect to Ollama
try:
    ollama = OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key='ollama',  # Required, but ignored by Ollama
    )
except Exception as e:
    print(f"Failed to initialize Ollama client: {e}")
    # Add a fallback or exit if the client can't be created
    exit()

# Define the system prompt for the summarization task
system_prompt = """
You are a witty assistant that analyzes the content of a website.
Provide a short, humorous summary, ignoring text that might be navigation-related.
Respond in markdown format. Do not wrap the markdown in a code block.
"""

# Define the user prompt prefix
user_prompt_prefix = """
Here is the content of a website.
Provide a short summary of this website.
If it includes news or announcements, please summarize these as well.
"""

def create_messages_for_website(website_content):
    """Creates the message structure for the Ollama API call."""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_prefix + website_content},
    ]

def summarize_with_ollama(url):
    """
    Summarizes the content of a given URL using Ollama.

    Args:
        url (str): The URL of the website to summarize.

    Returns:
        str: The summary of the website, or an error message.
    """
    try:
        website_content = fetch_website_contents(url)
        if not website_content:
            return "Could not retrieve content from the website."

        messages = create_messages_for_website(website_content)

        response = ollama.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {e}"

def display_summary(url):
    """Retrieves and displays the summary in Markdown format."""
    summary = summarize_with_ollama(url)
    display(Markdown(summary))

if __name__ == '__main__':
    # Example usage:
    # Make sure to have the Ollama server running before executing.
    # From your terminal, run: `ollama serve`
    # You might also need to pull the model: `ollama pull llama3.2`

    # To run this from the command line, you can use:
    # `uv run python week1/solution.py`
    
    # You will need to replace the display call with a simple print,
    # as display is for Jupyter environments.
    
    test_url = "https://example.com"
    print(f"Attempting to summarize {test_url} using Ollama...")
    summary_text = summarize_with_ollama(test_url)
    print("--- Summary ---")
    print(summary_text)
    print("--- End Summary ---")

    # sbx daemon run
    # sbx run --kit "git+https://github.com/docker/sbx-kits-contrib.git#dir=pi" pi

