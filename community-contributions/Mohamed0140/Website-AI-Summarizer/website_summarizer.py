import os

from dotenv import load_dotenv
from scraper import fetch_website_contents
from IPython.display import Markdown, display
from openai import OpenAI

load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

if not api_key:
    print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
elif not api_key.startswith("sk-proj-"):
    print("An API key was found, but it doesn't start sk-proj-; please check you're using the right key - see troubleshooting notebook")
elif api_key.strip() != api_key:
    print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
else:
    print("API key found and looks good so far!")

system_prompt = """
You are an assistant that analyzes the contents of a website,
and provides a short, concise, clear summary, ignoring text that might be navigation related.
Respond in markdown. Do not wrap the markdown in a code block - respond just with the markdown.
"""

user_prompt_prefix = """
Here are the contents of a website.
Provide a short summary of this website.
If it includes news or announcements, then summarize these too.

"""

def message_for(website):

    return [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt_prefix + website}]

def summarize(url):
    website = fetch_website_contents(url)
    response = client.chat.completions.create(
        model = "gpt-4.1-mini",
        messages = message_for(website)
    )
    return response.choices[0].message.content



