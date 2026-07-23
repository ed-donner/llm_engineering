import os
from ollama import chat
import requests
from bs4 import BeautifulSoup

MODEL = "gemma2:2b"

def fetch_url_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for tags in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript"]):
            tags.decompose()
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines()]
        text = "\n".join(line for line in lines if line)
        return text or ""
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return ""

def summarize(url):
    content = fetch_url_content(url)
    system_prompt = """
    You are reading this website just like any regular visitor would. 
    As you read, point out anything that doesn't make sense, feels confusing, lacks enough explanation, seems inconsistent, or leaves you with unanswered questions. 
    Explain each observation in simple language.
    """

    user_prompt = """
    Point out the issues in the content.
    """

    llm_payload = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt+content}
    ]
    response = chat(MODEL, llm_payload,stream=True)
    for chunk in response:
        piece = chunk["message"]["content"]
        print(piece, end="", flush=True)
    print()

url = "https://geeksforgeeks.org/python-programming-language/"
summarize(url)