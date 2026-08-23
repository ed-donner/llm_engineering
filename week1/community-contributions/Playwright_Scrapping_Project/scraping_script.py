import os
import openai
from IPython.display import Markdown, display
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")  # Or set it directly

def scrape_website(url):
    # Code to scrape a website using Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        content = page.content()
        browser.close()
        return content

def summarize_content(html_content):
    #Get only the text parts of the webpage
    soup = BeautifulSoup(html_content, 'html.parser')
    summary_text = soup.get_text(separator=' ', strip=True)
    # Code to summarize using OpenAI API
    system_prompt = ("You summarize html content as markdown.")
    user_prompt = (
        "You are a helpful assistant. Summarize the following HTML webpage content in markdown with simple terms:\n\n"
        + summary_text
    )
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": user_prompt}]
    )
    return response.choices[0].message.content

def save_markdown(summary, filename="summary.md", url=None):
    #Open the file summary.md
    with open(filename, "w", encoding="utf-8") as f:
        if url:
            f.write(f"# Summary of [{url}]({url})\n\n")
        else:
            f.write("# Summary\n\n")
        f.write(summary.strip())

# 4. Main Logic
def main():
    url = input("Enter the URL to summarize: ").strip()
    html = scrape_website(url)
    summary = summarize_content(html)
    save_markdown(summary, filename="summary.md", url=url)
    print("✅ Summary saved to summary.md")

# 5. Entry Point
if __name__ == "__main__":
    main()