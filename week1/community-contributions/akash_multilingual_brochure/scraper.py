import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

def fetch_website_links(url: str) -> list[str]:
    """Fetch all clean internal and external http links from a webpage."""
    if not url.startswith("http"):
        url = f"https://{url}"
    
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching links from {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(url, href)
        parsed_full = urlparse(full_url)
        
        if parsed_full.scheme in ("http", "https") and not href.startswith(("#", "mailto:", "tel:")):
            links.add(full_url)

    return list(links)

def fetch_website_contents(url: str) -> str:
    """Fetch and clean main text content from a webpage."""
    if not url.startswith("http"):
        url = f"https://{url}"

    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        response.raise_for_status()
    except Exception as e:
        return f"Error fetching content from {url}: {e}"

    soup = BeautifulSoup(response.text, "html.parser")
    
    for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    cleaned_lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 20]
    extracted_text = "\n".join(cleaned_lines[:200])

    return extracted_text if extracted_text else f"No meaningful text found on {url}"