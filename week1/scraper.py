from bs4 import BeautifulSoup
import requests


# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]


def fetch_website_links(url):
    """
    Return the links on the webiste at the given url
    I realize this is inefficient as we're parsing twice! This is to keep the code in the lab simple.
    Feel free to use a class and optimize it!
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]

def extract_main_text(soup, min_length=80):
    paragraphs = soup.find_all("p")
    # Only keep paragraphs that are long enough
    text_paragraphs = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) >= min_length]
    return "\n\n".join(text_paragraphs)

def clean_soup(soup):
    # Remove script, style, and common UI elements
    for tag in soup(["script", "style", "header", "footer", "nav", "aside", "form", "iframe", "input"]):
        tag.decompose()
    return soup
    
def extract_best_div(soup):
    candidates = soup.find_all("div")
    best_score = 0
    best_div = None
    for div in candidates:
        text = div.get_text(" ", strip=True)
        link_text = " ".join(a.get_text(strip=True) for a in div.find_all("a"))
        score = len(text) - len(link_text)  # penalize link-heavy divs
        if score > best_score:
            best_score = score
            best_div = div
    return best_div.get_text("\n", strip=True) if best_div else ""


def fetch_website_content(url, min_paragraph_length=80):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.content, "html.parser")

    title = soup.title.string if soup.title else "No title"

    soup = clean_soup(soup)

    # Try semantic containers first
    content = soup.find("main") or soup.find("article")
    if content:
        text = content.get_text("\n", strip=True)
    else:
        text = extract_best_div(soup)
        if not text:
            text = extract_main_text(soup, min_paragraph_length)

    return title + "\n\n" + text

