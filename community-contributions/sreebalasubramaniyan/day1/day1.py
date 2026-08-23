import os
from dotenv import load_dotenv
from openai import OpenAI

from scrapper import fetch_website_content

load_dotenv()

OPEN_ROUTER_URL = "https://openrouter.ai/api/v1"
api_key = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url=OPEN_ROUTER_URL,
    api_key=api_key
)
def chat(prompt):
    try:
        response = client.chat.completions.create(
        model="cohere/north-mini-code:free",
            messages=prompt
        )

        res = (response.choices[0].message.content)

    except Exception as e:
        res = ("Error:", e)

    return res
url = input("Enter the url for summary: ")
content = fetch_website_content(url)
def makeprompt(content):
    system_prompt = """
        You are a snarky assistant that analyzes the contents of a website,
        and provides a short, snarky, humorous summary, ignoring text that might be navigation related.
        Respond in markdown. Do not wrap the markdown in a code block - respond just with the markdown.
        """
    user_prompt_prefix = """k
    Here are the contents of a website.
    Provide a short summary of this website.
    If it includes news or announcements, then summarize these too.
    """
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_prefix + content}
    ]

prompt = makeprompt(content)

summary = chat(prompt)

print(summary)