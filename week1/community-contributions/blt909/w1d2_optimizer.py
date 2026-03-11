# imports
import os, sys
from openai import OpenAI
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import requests

load_dotenv(override=True)

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(os.path.dirname(current))
sys.path.append(parent)

from scraper import fetch_website_contents

class Optimizer:  
    analysis_system_prompt = """
    You are an assistant that reads the contents of a webpage, discovers the language of the page.
    You will provide an SEO optimized version of the webpage's content, ignoring text that might be navigation related.
    Respond in the same language while keeping the overall content, structure, tone of the original website. 
    Do not wrap the markdown in a code block - respond just with the markdown.
    Do not giving insights about the page, just the SEO optimized version of the content.
    Do not summarize the content, just provide the SEO optimized version of the content.
    """

    analysis_user_prompt = """
    Here are the contents of a webpage.
    Provide an optimized version of the page in the language of the page.

    """

    evaluation_system_prompt = """
    You are an assistant that compares differents versions of a webpage's content optimizationand provides a comparison of the two.
    You will receive the original content of the webpage, the optimized version of the content by llama3.2 and the optimized version of the content by deepseek-r1:1.5b.
    You will rate the two optimized versions on a scale of 1 to 10.
    You will also provide your own SEO optimized version of the webpage's content, ignoring text that might be navigation related.
    Respond in the same language while keeping the overall content, structure, tone of the original website. 
    Do not wrap the markdown in a code block - respond just with the markdown.
    Do not give insights about the page, just the SEO optimized version of the content.
    Do not summarize the content, just provide the SEO optimized version of the content.
    """

    evaluation_user_prompt = """
    Here are the contents of a webpage.
    Provide an evaluation of the two optimized versions on a scale of 1 to 10.
    Then Provide an optimized version of the page in the language of the page.
    ## Original content:
    {original_content}
    ## llama3.2 optimized content:
    {llama3_content}
    ## deepseek-r1:1.5b optimized content:
    {deepseek_content}
    """
    def __init__(self) -> None:
        pass

    def scrape(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        soup.prettify()
        title = soup.title.string if soup.title else "No title found"
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            
            text = soup.body.get_text(separator=" ", strip=True)
        else:
            text = ""
        return (title + "\n\n" + text)

    def optimize_content(self, content, model):
        OLLAMA_BASE_URL = "http://localhost:11434/v1"
        ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key='ollama')
        messages = [
            {"role": "system", "content": self.analysis_system_prompt},
            {"role": "user", "content": self.analysis_user_prompt + content}
        ]
        response = ollama.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content

    def evaluate_content(self, model, original_content, llama3_content, deepseek_content):
        if model=="gpt-5-nano":
            openai = OpenAI()
        else:
            GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
            openai=OpenAI(base_url=GEMINI_BASE_URL, api_key=os.getenv("GOOGLE_API_KEY"))
        messages = [
            {"role": "system", "content": self.evaluation_system_prompt},
            {"role": "user", "content": self.evaluation_user_prompt.format(original_content=original_content, llama3_content=llama3_content, deepseek_content=deepseek_content)}
        ]
        response = openai.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content
