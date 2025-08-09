import os
import requests
from bs4 import BeautifulSoup
import ollama

MODEL = "llama3.2:1b"

system_prompt = "You are an assistant that analyzes the contents of a website and provides a short summary,ignoring text that might be navigation related. Respond in markdown."

def user_prompt_for(website):
    user_prompt = f"You are looking at a website titled {website.title}\n"
    user_prompt += "The contents of this website is as follows; please provide a short summary of this website in markdown. If it includes news or announcements, then summarize these too.\n\n"
    user_prompt += website.text
    return user_prompt

def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_for(website)}
    ]

class Website:
    def __init__(self, url):
        self.url = url
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        for irrelevant in soup(["script", "style", "img", "input"]):
            irrelevant.decompose()
        self.text = soup.get_text(separator="\n", strip=True)

def summarize(url):
    website = Website(url)
    response = ollama.chat(
        model=MODEL,
        messages=messages_for(website)
    )
    return response['message']['content']


print(summarize("https://stephango.com"))
