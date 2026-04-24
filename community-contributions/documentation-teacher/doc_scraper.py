from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse

# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_doc_contents(url, max_chars=3000):
    """
    Return the title and contents of the documentation page at the given url;
    Optimized for technical documentation sites
    """
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        
        title = soup.title.string if soup.title else "No title found"
        
        # Remove irrelevant elements
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input", "nav", "footer", "header"]):
                irrelevant.decompose()
            
            # Try to find main content area (common in documentation sites)
            main_content = soup.find("main") or soup.find("article") or soup.body
            text = main_content.get_text(separator="\n", strip=True)
        else:
            text = ""
        
        return (title + "\n\n" + text)[:max_chars]
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"


def fetch_doc_links(url):
    """
    Return the links on the documentation website at the given url
    Returns both the link text and href for better context
    """
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        links = []
        
        for link in soup.find_all("a"):
            href = link.get("href")
            text = link.get_text(strip=True)
            
            if href and text:
                # Convert relative URLs to absolute
                if href.startswith("/"):
                    href = urljoin(base_url, href)
                elif not href.startswith("http"):
                    href = urljoin(url, href)
                
                links.append({"text": text, "url": href})
        
        return links
    except Exception as e:
        return []


def is_same_domain(url1, url2):
    """Check if two URLs are from the same domain"""
    return urlparse(url1).netloc == urlparse(url2).netloc
