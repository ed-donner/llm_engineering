import os
from dotenv import load_dotenv
from ollama import chat
import requests
from bs4 import BeautifulSoup

MODEL = "qwen2.5:3b"
load_dotenv(override=True)


# user_prompt = """
# Please explain what this code does and give alternative ways to implement it and choose the best way to implement it:
#     def _parse_ollama_json(self, response: str) -> dict:
#         response = response.strip()
#         if response.startswith("```json"):
#             response = response[7:]
#         if response.startswith("```"):
#             response = response[3:]
#         if response.endswith("```"):
#             response = response[:-3]
#         response = response.strip()
#         response = response.replace('\u201c', '"').replace('\u201d', '"')
#         response = response.replace('\u2018', "'").replace('\u2019', "'")
#         response = response.replace('\u2013', '-').replace('\u2014', '-')
# """

# system_prompt = """You are an experience software engineer who explains code in a very brief way.
# Your behaviour should be snarky since you are strict about best practices. 
# Itemise your responses and give a conclusive resopnse when done.
# """

# llm_payload = [
#     {"role": "system", "content": system_prompt},
#     {"role": "user", "content": user_prompt}
# ]

# response = chat(MODEL, llm_payload,stream=True)
# for chunk in response:
#     piece = chunk["message"]["content"]
#     print(piece, end="", flush=True)

# print()


# Web Scraping Exercise

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
    system_prompt = """You are a careful technical person who checks the content of a website for accuracy and completeness and most points out the issues in the content.
    You are given the content and you need to point out the issues in the content.
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








