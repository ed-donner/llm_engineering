import os
from openai import OpenAI
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

OLLAMA_BASE_URL = "http://localhost:11434/v1"

def scrape_website(url: str):
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=10000)
            html = page.content()
            browser.close()
    except Exception as e:
        return f"Failed to access page: {e}"

    soup = BeautifulSoup(html, "html.parser")

    # remove unnecessary tags
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    # look for the most relevant parts of the webpage
    main = soup.find("main") or soup.find("article") or soup
    text = main.get_text(separator=' ', strip=True)[:3000]

    messages = [
        {"role": "system", "content": "You are a snarky assistant that summarizes websites."},
        {"role": "user", "content": f"Provide a brief summary of this website:\n\n{text}"}
    ]

    ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key='ollama')
    response = ollama.chat.completions.create(model="llama3.2", messages=messages)
    return response.choices[0].message.content


def display_summary(url: str):
    summary = scrape_website(url)
    print(summary)


if __name__ == "__main__":
    url = input("Enter URL to summarize: ").strip()
    display_summary(url)
    