from bs4 import BeautifulSoup
import requests
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown

url="https://www.fromthepage.com/"

OLLAMA_BASE_URL = "http://localhost:11434/v1"

ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key="anything")
console=Console()

def fetch_links(url):
    links=""

    response=requests.get(url)

    if response.status_code==200:
        soup=BeautifulSoup(response.text,"html.parser")
        for link in soup.find_all("a"):
            href=link.get("href")
            if href:
                links+=href+"\n"
    return links

def relevant_links(url):
    link=fetch_links(url)

    systemPrompt=f"Use context: {link} to find relevant links"

    userPrompt=f"Find all relevant links to the webpage {url} and extract vital information from them"
    response=ollama.chat.completions.create(model="llama3.2",messages=[
            {
                "role":"system",
                "content":systemPrompt
            },
            {
                "role":"user",
                "content":userPrompt
            }
        ])

    response.choices[0].message.content
    rel_link=response.choices[0].message.content.strip()
    return rel_link

def create_brochure(url):

    info=relevant_links(url)
    userPrompt=f"Create a brochure for the organization/company using all information avaiable in {url} and {info}"
    systemPrompt="You are a history nerd fascinated with written accords of things long gone. You are good at summarising and conversations, currently acting as a salesman for the organization. Subtly but incesstantly nudge the reader to give transcribing a go. Start with 'If you like...'"
    response=ollama.chat.completions.create(model="llama3.2",messages=[
            {
                "role":"system",
                "content":systemPrompt
            },
            {
                "role":"user",
                "content":userPrompt
            }
        ],
        temperature=1.2
        )

    return response.choices[0].message.content.strip()

brochure=create_brochure(url)

console.print(Markdown(brochure))