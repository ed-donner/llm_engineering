import os

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from playwright.sync_api import sync_playwright


load_dotenv(override=True)

MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2")
MODEL_BASE_URL = os.getenv("MODEL_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "ollama")


SYSTEM_PROMPT = """
You are an expert webpage summarizer.

Analyze the provided webpage content and explain the
important information clearly and concisely.

Ignore navigation, advertisements, menus, footers,
and unrelated content.

Do not invent information.

Respond in markdown without wrapping it in a code block.
"""


def scrape_website(url: str) -> str:
    """Fetch and return the rendered HTML content of a website."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)

        try:
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)
            body_text = page.locator("body").inner_text().lower()
            verification_markers = [
                "enable javascript",
                "enable cookies",
                "verify you are human",
                "checking your browser",
                "just a moment",
            ]

            if any(marker in body_text for marker in verification_markers):
                raise RuntimeError("Website requires browser verification.")

            return page.content()

        finally:
            browser.close()


def extract_content(html: str) -> str:
    """Extract and return the relevant text content from webpage HTML."""

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(
        [
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "noscript",
        ]
    ):
        tag.decompose()

    content_element = soup.find("main") or soup.find("article") or soup

    return " ".join(content_element.get_text(separator=" ", strip=True).split())


def user_prompt_for(text):
    """Build the user prompt containing the extracted website content."""

    user_prompt = "You are looking at the contents of a website."

    user_prompt += (
        "\nPlease provide a concise summary of the website in markdown."
        "\nFocus on the main information, important facts, and key takeaways."
        "\nIgnore navigation, advertisements, and unrelated content."
        "\n\nThe website contents are as follows:\n\n"
    )

    user_prompt += text

    return user_prompt


def summarize_content(client: OpenAI, text: str) -> str:
    """Generate a markdown summary of the extracted website content."""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt_for(text)},
        ],
    )

    return response.choices[0].message.content


def save_markdown(summary: str, url: str, filename: str = "summary.md") -> None:
    """Save the generated summary to a Markdown file."""

    with open(filename, "w", encoding="utf-8") as file:
        file.write(f"# Summary of [{url}]({url})\n\n")
        file.write(summary.strip())


def main():
    """Orchestrate the website scraping, extraction, summarization, and saving workflow."""

    url = input("Enter URL to summarize: ").strip()
    client = OpenAI(base_url=MODEL_BASE_URL, api_key=API_KEY)

    try:
        print("Fetching webpage...")
        html = scrape_website(url)

        print("Extracting content...")
        text = extract_content(html)

        if not text:
            raise RuntimeError("No meaningful content found.")

        print(f"Extracted {len(text)} characters.")

        print("Generating summary...")
        summary = summarize_content(client, text)

        save_markdown(summary, url)
        print("Summary saved to summary.md")

    except Exception as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
