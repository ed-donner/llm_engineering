import ollama
import os
import requests

from bs4 import BeautifulSoup
from IPython.display import Markdown, display

MODEL = "llama3.2:3b-instruct-q8_0"

messages = [
    {"role": "user", "content": "Describe some of the business applications of Generative AI"}
]

# response = ollama.chat(model=MODEL, messages=messages)
# print(response['message']['content'])
class Website:

    def __init__(self, url):
        """
        Create this Website object from the given url using the BeautifulSoup library
        """
        self.url = url
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        try:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
        except:
            pass
        self.text = soup.body.get_text(separator="\n", strip=True)

system_prompt = "You are an assistant that analyzes the contents of a website \
and provides a short summary, ignoring text that might be navigation related. \
Respond in markdown."

def user_prompt_for(website):
    user_prompt = f"You are looking at a website titled {website.title}"
    user_prompt += "\nThe contents of this website is as follows; \
    please provide a short summary of this website in markdown. \
    If it includes news or announcements, then summarize these too.\n\n"
    user_prompt += website.text
    return user_prompt

def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_for(website)}
    ]

def summarize(url):
    website = Website(url)
    response = ollama.chat(
        model = MODEL,
        messages = messages_for(website)
    )
    return response['message']['content']

def display_summary(url):
    summary = summarize(url)
    print(summary)

display_summary("https://mike-tupper.com/")