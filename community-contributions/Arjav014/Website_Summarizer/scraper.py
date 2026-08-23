import requests
from bs4 import BeautifulSoup

def scrape_website(url: str) -> str:
    """
    Scrapes the text content of a given website, removing styling, scripts,
    navigation, and footers to return clean content for summarization.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Error fetching the website: {e}"
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Remove script, style, nav, and footer elements
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()
        
    # Extract visible text content
    text = soup.get_text(separator="\n")
    
    # Clean up whitespace and empty lines
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    clean_text = "\n".join(chunk for chunk in chunks if chunk)
    
    # Prepend the website title if available
    title = soup.title.string.strip() if soup.title else "No Title"
    return f"Title: {title}\n\n{clean_text}"
