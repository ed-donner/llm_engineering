from dotenv import load_dotenv
from openai import OpenAI
from playwright.sync_api import sync_playwright
from .utils.scrape_webpage import get_page, get_page_body
import re
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")


client = OpenAI()


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    content = get_page_body(page)
    browser.close


messages = [
    {
        "role": "system",
        "content": "You are a great intelligent poet but sarcastic and funny",
    },
    {
        "role": "user",
        "content": f"Based on the website create a poem about it, make the content funny {content}",
    },
]

completions = client.chat.completions.create(model="gpt-4.1-nano", messages=messages)

print(completions.choices[0].message.content)
