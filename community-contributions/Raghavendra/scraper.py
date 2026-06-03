from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse

# Standard headers to fetch a website
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36"
    )
}


def fetch_website_contents(url, max_chars=2000):
    """
    Return the title + cleaned body text from a web page.
    Automatically removes scripts, styles, imgs, nav, footer, etc.
    Truncates to max_chars.
    """
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return f"Failed to fetch {url}: {e}"

    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else "No title found"

    # Remove irrelevant elements
    remove_tags = ["script", "style", "img", "input", "nav", "footer", "form"]
    for tag in soup(remove_tags):
        tag.decompose()

    # Get the text
    text = soup.get_text(separator="\n", strip=True)
    text = "\n".join(line for line in text.splitlines() if line.strip())  # remove blank lines

    return (title + "\n\n" + text)[:max_chars]


def fetch_website_links(url):
    """
    Return cleaned list of valid, absolute links on given page.
    Filters out:
    - email (mailto:)
    - phone (tel:)
    - pdf, files, images
    - login, privacy, terms, cookie pages
    - social media links (optional)
    """
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch links from {url}: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    raw_links = [a.get("href") for a in soup.find_all("a") if a.get("href")]

    cleaned_links = []
    for link in raw_links:
        # Convert relative → full absolute URL
        full_url = urljoin(url, link)

        # Remove tracking fragments (?ref= etc.)
        parsed = urlparse(full_url)
        full_url = parsed.scheme + "://" + parsed.netloc + parsed.path

        # Filters to ignore unwanted links
        skip_keywords = [
            "mailto:", "tel:", ".pdf", ".jpg", ".png", ".jpeg",
            "privacy", "terms", "login", "signup", "cookie"
        ]
        if any(skip in full_url.lower() for skip in skip_keywords):
            continue

        if full_url not in cleaned_links:
            cleaned_links.append(full_url)

    return cleaned_links
