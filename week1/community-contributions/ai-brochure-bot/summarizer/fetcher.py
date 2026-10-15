import requests
from bs4 import BeautifulSoup
import logging
import os

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_web_content(url):
    """Fetches the webpage content and extracts links."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise error for failed requests
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract all links
        links = [a['href'] for a in soup.find_all('a', href=True)]
        logger.info(f"Fetched {len(links)} links from {url}")
        return links
    except requests.RequestException as e:
        logger.error(f"Failed to fetch content from {url}: {e}")
        return []

def format_links(base_url, links):
    """Converts relative links to absolute URLs and filters irrelevant ones."""
    filtered_links = []
    for link in links:
        if link.startswith("/"):
            link = base_url.rstrip("/") + link
        if "contact" not in link.lower() and "privacy" not in link.lower():
            filtered_links.append(link)
    
    return filtered_links
