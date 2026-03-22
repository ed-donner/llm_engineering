"""
Recipe Web Scraper Module

Handles web scraping logic for extracting recipe content from URLs.
"""

import requests
from bs4 import BeautifulSoup

# HTTP headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


class RecipeScraper:
    """
    Scrapes recipe content from popular recipe websites.
    Handles multiple site formats and extracts structured recipe data.
    """
    
    def __init__(self, url):
        """Initialize scraper with a recipe URL."""
        self.url = url
        self.title = ""
        self.raw_text = ""
        self.scrape()
    
    def scrape(self):
        """Scrape recipe from the URL."""
        try:
            response = requests.get(self.url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_tag = soup.find('h1') or soup.find('title')
            self.title = title_tag.get_text(strip=True) if title_tag else "Recipe"
            
            # Extract full text content (LLM will parse it)
            full_text = soup.get_text(separator="\n", strip=True)
            self.raw_text = full_text[:10000]  # Limit to first 10k chars
            
        except Exception as e:
            print(f"Error scraping recipe: {e}")
            self.title = "Error loading recipe"
            self.raw_text = ""
    
    def get_recipe_text(self):
        """Return formatted recipe text for LLM processing."""
        return f"Recipe Title: {self.title}\n\nURL: {self.url}\n\nContent:\n{self.raw_text[:8000]}"

