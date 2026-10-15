import requests
from bs4 import BeautifulSoup

def fetch_web_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract readable text from the web page (ignoring scripts, styles, etc.)
        page_text = soup.get_text(separator=' ', strip=True)
        
        return page_text[:5000]  # Limit to 5000 chars (API limitation)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None

if __name__ == "__main__":
    url = "https://en.wikipedia.org/wiki/Natural_language_processing"
    content = fetch_web_content(url)
    print(content[:500])  # Print a sample of the content
