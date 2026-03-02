from openai import OpenAI
from bs4 import BeautifulSoup
import requests

# ---------------------------
# OLLAMA CONFIG
# ---------------------------

OLLAMA_BASE_URL = "http://localhost:11434/v1"

ollama = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama"  # required but ignored by Ollama
)

# ---------------------------
# AI PROMPTS VARIABLES
# ---------------------------

system_prompt = """
You are a snarky assistant that analyzes website content.

Return:
- A bold subject line
- A short humorous summary
- Use clean markdown formatting

Do NOT wrap your response inside a markdown code block.
"""

user_prompt = """
Summarize this website with a perfect subject line.
Keep it short, snarky, and funny.
"""

# ---------------------------
# WEBSITE SCRAPER FUNCTION
# ---------------------------

headers = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_website_contents(url):
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    title = soup.title.string if soup.title else "No title found"

    if soup.body:
        for tag in soup.body(["script", "style", "img", "input", "nav", "footer"]):
            tag.decompose()

        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""

    return (title + "\n\n" + text)[:2000]


# ---------------------------
# LLM CALL FUNCTION
# ---------------------------

def summarize(url):
    website = fetch_website_contents(url)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": website + "\n\n" + user_prompt}
    ]

    response = ollama.chat.completions.create(
        model="llama3.2:1b",
        messages=messages,
        temperature=0.7
    )

    return response.choices[0].message.content


# ---------------------------
# MAIN PROGRAM
# ---------------------------

def main():
    print("🌐 Website Summarizer (Powered by Ollama)")
    print("-" * 40)

    url = input("Enter website URL: ").strip()

    if not url.startswith("http"):
        url = "https://" + url

    try:
        print("\nFetching and summarizing...\n")
        summary = summarize(url)
        print(summary)
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    main()