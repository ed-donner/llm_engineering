import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool

@tool
def url_scraper(url: str) -> str:
    """Extract text content from a specific URL. Input should be a valid URL string."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Get text
        text = soup.get_text(separator="\n")

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        return text[:4000]  # Limit to 4000 chars for context window safety
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"
