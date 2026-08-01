import os
from openai import OpenAI
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

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
        {"role": "system", "content": "You are a helpful assistant that summarizes websites."},
        {"role": "user", "content": f"Provide a brief summary of this website:\n\n{text}"}
    ]

    openai = OpenAI()
    response = openai.chat.completions.create(model="gpt-5-nano", messages=messages)
    return response.choices[0].message.content


def display_summary(url: str):
    summary = scrape_website(url)
    print(summary)


if __name__ == "__main__":
    url = input("Enter URL to summarize: ").strip()
    display_summary(url)
    