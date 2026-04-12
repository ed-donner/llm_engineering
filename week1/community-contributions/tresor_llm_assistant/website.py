# -*- coding:utf-8 -*-

import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from IPython.display import Markdown, display
from IPython import get_ipython
from openai import OpenAI

load_dotenv()

# OpenAI / Ollama client
openai = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

system_prompt = """
You summarize website content.
Ignore navigation, menus, and boilerplate text.
Focus on meaningful content.
Respond in markdown.
"""

class Website:
    """A class to represent a website and extract + summarize its content."""

    def __init__(self, url):
        self.url = url

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        self.soup = BeautifulSoup(response.text, 'html.parser')
        self.title = self.soup.title.string.strip() if self.soup.title else 'No Title Found'

        for tag in self.soup(['script', 'style', 'meta', 'link', 'noscript']):
            tag.decompose()

        self.text = self.soup.get_text(separator=' ', strip=True)
        self.content = f"Title: {self.title}\n\nText: {self.text}"

    def user_prompt_for(self):
        return (
            f"You are looking at a website titled '{self.title}'.\n\n"
            "The contents of this website are below.\n"
            "Provide a short summary in markdown.\n"
            "If it includes news or announcements, summarize those too.\n\n"
            f"{self.content}"
        )

    def messages_for(self):
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self.user_prompt_for()}
        ]

    def summarize(self, model='llama3.2'):
        response = openai.chat.completions.create(
            model=model,
            messages=self.messages_for(),
        )
        return response.choices[0].message.content

    def display_summary(self, model='llama3.2'):
        summary = self.summarize(model=model)

        if get_ipython():
            display(Markdown(summary))
        else:
            print(summary)
