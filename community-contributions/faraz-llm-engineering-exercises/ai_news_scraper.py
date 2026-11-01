# AI News Scraper Module
# ----------------------
import re
import time
from bs4 import BeautifulSoup
from curl_cffi import requests

# Whole-word regex matching AI terms and concepts
AI_PATTERN = re.compile(
    r"\b(ai|artificial intelligence|generative ai|genai|llm|llms|large language model|"
    r"openai|chatgpt|gpt-4|gpt-4o|anthropic|claude|deepmind|gemini|copilot|nvidia|npu|"
    r"h100|b200|semiconductors?|deepseek|moonshot|mistral|hugging face|machine learning|"
    r"neural network|robotaxis?)\b",
    re.IGNORECASE
)


def fetch_website_headlines(url):
    """
    Fetches AI-related headlines from any website URL.
    
    Args:
        url (str): The URL of the website to scrape.
        
    Returns:
        list[str]: A list of clean AI headline strings.
    """
    # 1. Fetch webpage using browser impersonation (retries up to 3 times)
    response = None
    for _ in range(3):
        try:
            response = requests.get(url, impersonate="chrome120", timeout=15)
            if response.status_code == 200:
                break
        except Exception:
            time.sleep(1)

    if not response or not response.text:
        return []

    # 2. Parse HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")
    
    headlines = []
    
    # 3. Extract headline strings matching AI keywords
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "a"]):
        text = tag.get_text(strip=True)
        text = re.sub(r"\s+", " ", text)
        
        # Fallback to title attribute if tag text is very short
        if len(text) < 15 and tag.get("title"):
            text = tag.get("title").strip()
            
        if text and len(text) > 15 and text not in headlines:
            if not re.search(r"/(Bloomberg|Getty|AP|NurPhoto|Reuters)", text):
                if AI_PATTERN.search(text):
                    headlines.append(text)
    
    # 4. Return the list of headlines
    return headlines
