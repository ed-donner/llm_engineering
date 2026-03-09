import re
import time
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from langchain_core.documents import Document

# Optional: Selenium (install selenium, webdriver-manager)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

# Thresholds for JS detection
MIN_STATIC_CONTENT_CHARS = 300
SELENIUM_WAIT_SECONDS = 3


def _get_body_text(html: str) -> str:
    """Extract body text only (for JS detection)."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    if soup.body:
        return soup.body.get_text(separator=" ", strip=True)
    return ""


def _has_spa_indicators(html: str) -> bool:
    """Check for common SPA/JS framework indicators in raw HTML."""
    lower = html.lower()
    patterns = [
        'id="root"',
        'id="app"',
        'id=\'root\'',
        'id=\'app\'',
        "__next_data__",
        "data-reactroot",
        "ng-version",
        "v-cloak",
        "vue-app",
        "react-root",
    ]
    return any(p in lower for p in patterns)


def is_js_rendered(html: str, url: str = "") -> bool:
    """
    Heuristic: page is likely JS-rendered if:
    1. Body text is very short (< MIN_STATIC_CONTENT_CHARS)
    2. AND (has SPA indicators OR body is mostly empty)
    """
    body_text = _get_body_text(html)
    text_len = len(body_text)

    if text_len >= MIN_STATIC_CONTENT_CHARS:
        return False

    if _has_spa_indicators(html):
        return True

    # Very little content and no clear structure
    if text_len < 100:
        return True

    return False


def extract_headers_and_content(html: str) -> tuple[list[str], str]:
    """
    Extract (list of headers), (body text).
    Headers: ["H1: Title", "H2: Section", ...]
    Body: plain text, script/style removed.
    """
    soup = BeautifulSoup(html, "html.parser")

    headers_list = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text = tag.get_text(strip=True)
        if text:
            headers_list.append(f"{tag.name.upper()}: {text}")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    body = soup.get_text(separator="\n", strip=True)
    body = re.sub(r"\n\n+", "\n\n", body).strip()

    return headers_list, body


def page_to_document(url: str, html: str, title: str = "") -> Document:
    """
    Create a LangChain Document with headers and content as separate fields.
    page_content combines both for embedding/retrieval.
    metadata holds source, title, headers, body.
    """
    headers_list, body = extract_headers_and_content(html)
    if not title:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string if soup.title and soup.title.string else "No title"

    page_content = "Headers:\n" + "\n".join(headers_list) + "\n\nContent:\n" + body

    return Document(
        page_content=page_content,
        metadata={
            "source": url,
            "title": title,
            "headers": headers_list,
            "body": body,
        },
    )


def fetch_html_requests(url: str) -> str:
    """Fetch raw HTML via requests (no JS execution)."""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text


def fetch_html_selenium(url: str) -> str:
    """Fetch rendered HTML via Selenium (JS executed)."""
    if not SELENIUM_AVAILABLE:
        raise RuntimeError("Selenium not installed. pip install selenium webdriver-manager")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(url)
        time.sleep(SELENIUM_WAIT_SECONDS)
        return driver.page_source
    finally:
        driver.quit()


def load_page(url: str, force_selenium: bool = False) -> Document:
    """
    Load a single page into a Document.
    - Tries requests first.
    - If is_js_rendered(html), falls back to Selenium.
    - Uses headers + content extraction and page_to_document.
    """
    if force_selenium:
        html = fetch_html_selenium(url)
    else:
        html = fetch_html_requests(url)
        if is_js_rendered(html, url):
            html = fetch_html_selenium(url)

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string if soup.title and soup.title.string else ""

    return page_to_document(url, html, title)


def load_pages_from_url(
    url: str,
    follow_links: bool = False,
    max_pages: int = 5,
    force_selenium: bool = False,
) -> list[Document]:
    """
    Load the main page and optionally follow links.
    JS check and Selenium fallback apply to each page.
    """
    docs = [load_page(url, force_selenium=force_selenium)]

    if not follow_links:
        return docs

    try:
        html = fetch_html_requests(url)
        if is_js_rendered(html, url) and SELENIUM_AVAILABLE:
            html = fetch_html_selenium(url)
    except Exception:
        return docs

    soup = BeautifulSoup(html, "html.parser")
    seen = {url}

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(url, href) if not href.startswith("http") else href
        if not full.startswith("http") or full in seen:
            continue
        seen.add(full)
        if len(docs) >= max_pages:
            break
        try:
            docs.append(load_page(full, force_selenium=force_selenium))
        except Exception:
            pass

    return docs