import os
import re
import time
import json
import hashlib
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup
import html2text
import trafilatura
from tqdm import tqdm
from pathlib import Path

# project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# knowledge base directory
KB_PATH = PROJECT_ROOT / "knowledge_base"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT = 20
CRAWL_DELAY = 1.0
MAX_PAGES_PER_SITE = 150


SITES = [
    {
        "name": "langchain",
        "start_urls": [
            "https://docs.langchain.com/oss/python/langchain/overview",
        ],
        "allowed_prefixes": [
            "https://docs.langchain.com/oss/python/langchain/",
        ],
        "output_dir": KB_PATH / "langchain",
        "main_selectors": ["main"],
    },
    {
        "name": "huggingface",
        "start_urls": [
            "https://huggingface.co/docs/transformers/index",
            "https://huggingface.co/docs/datasets/index",
        ],
        "allowed_prefixes": [
            "https://huggingface.co/docs/transformers/",
            "https://huggingface.co/docs/datasets/",
        ],
        "output_dir": KB_PATH / "huggingface",
        "main_selectors": ["main"],
    },
    {
        "name": "fastapi",
        "start_urls": [
            "https://fastapi.tiangolo.com/",
        ],
        "allowed_prefixes": [
            "https://fastapi.tiangolo.com/",
        ],
        "output_dir": KB_PATH / "fastapi",
        "main_selectors": ["main", "article", ".md-content"],
    },
    {
        "name": "python_docs",
        "start_urls": [
            "https://docs.python.org/3/tutorial/index.html",
            "https://docs.python.org/3/library/index.html",
        ],
        "allowed_prefixes": [
            "https://docs.python.org/3/",
        ],
        "output_dir": KB_PATH / "python_docs",
        "main_selectors": ["main", 'div[role="main"]', ".body", ".document"],
    },
]


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def normalize_url(url: str) -> str:
    url, _ = urldefrag(url)
    return url.rstrip("/")


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def allowed_url(url: str, allowed_prefixes: list[str]) -> bool:
    return any(url.startswith(prefix.rstrip("/")) for prefix in allowed_prefixes)


def safe_filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    if not path:
        path = "index"

    # replace disallowed characters
    path = re.sub(r"[^a-zA-Z0-9/_-]", "_", path)

    # keep folder structure but end with .md
    if path.endswith(".html"):
        path = path[:-5]
    if path.endswith(".htm"):
        path = path[:-4]

    if path.endswith("/"):
        path += "index"

    return path + ".md"


def fetch_page(url: str) -> str | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        if "text/html" not in response.headers.get("Content-Type", ""):
            return None
        return response.text
    except requests.RequestException:
        return None


def extract_links(html: str, base_url: str) -> set[str]:
    soup = BeautifulSoup(html, "lxml")
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        absolute = urljoin(base_url, href)
        absolute = normalize_url(absolute)

        if is_valid_url(absolute):
            links.add(absolute)

    return links


def remove_unwanted_elements(soup: BeautifulSoup) -> None:
    selectors = [
        "nav",
        "header",
        "footer",
        "aside",
        "script",
        "style",
        ".theme-doc-breadcrumbs",
        ".theme-doc-footer",
        ".table-of-contents",
        ".toc",
        ".sidebar",
        ".pagination-nav",
        ".breadcrumbs",
    ]

    for selector in selectors:
        for tag in soup.select(selector):
            tag.decompose()


def extract_main_content(html: str, url: str, main_selectors: list[str]) -> str:
    """
    Try:
    1. Specific main selectors
    2. trafilatura
    3. fallback to body
    """
    soup = BeautifulSoup(html, "lxml")
    remove_unwanted_elements(soup)

    for selector in main_selectors:
        main = soup.select_one(selector)
        if main:
            return str(main)

    extracted = trafilatura.extract(
        html,
        include_links=True,
        include_images=False,
        output_format="markdown",
        favor_recall=True,
        url=url,
    )
    if extracted:
        return extracted

    body = soup.body
    return str(body) if body else ""


def html_fragment_to_markdown(html_fragment: str) -> str:
    converter = html2text.HTML2Text()
    converter.ignore_images = True
    converter.ignore_emphasis = False
    converter.ignore_links = False
    converter.body_width = 0
    converter.single_line_break = False

    markdown = converter.handle(html_fragment)

    # clean extra noise
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    markdown = re.sub(r"[ \t]+\n", "\n", markdown)
    return markdown.strip()


def clean_markdown(markdown: str) -> str:
    lines = markdown.splitlines()
    cleaned = []

    skip_patterns = [
        r"^\s*Skip to main content\s*$",
        r"^\s*On this page\s*$",
        r"^\s*Edit this page.*$",
        r"^\s*Next.*$",
        r"^\s*Previous.*$",
        r"^\s*Table of contents\s*$",
    ]

    for line in lines:
        line = line.rstrip()

        if any(re.match(pattern, line, flags=re.IGNORECASE) for pattern in skip_patterns):
            continue

        cleaned.append(line)

    markdown = "\n".join(cleaned)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()
    return markdown


def save_markdown(output_dir, url, markdown):

    relative_path = safe_filename_from_url(url)

    file_path = Path(output_dir) / relative_path

    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    return str(file_path)


def save_metadata(output_dir: str, url: str, file_path: str) -> None:
    metadata_path = Path(output_dir) / "metadata.jsonl"
    record = {
        "url": url,
        "file_path": file_path.replace("\\", "/"),
        "sha1": hashlib.sha1(url.encode("utf-8")).hexdigest(),
    }

    with open(metadata_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def crawl_site(site_config: dict) -> None:
    name = site_config["name"]
    start_urls = [normalize_url(u) for u in site_config["start_urls"]]
    allowed_prefixes = [p.rstrip("/") for p in site_config["allowed_prefixes"]]
    output_dir = site_config["output_dir"]
    main_selectors = site_config.get("main_selectors", ["main"])

    ensure_dir(output_dir)

    visited = set()
    queue = list(start_urls)

    print(f"\n=== Crawling: {name} ===")
    progress = tqdm(total=MAX_PAGES_PER_SITE, desc=name)

    while queue and len(visited) < MAX_PAGES_PER_SITE:
        url = queue.pop(0)

        if url in visited:
            continue

        if not allowed_url(url, allowed_prefixes):
            continue

        visited.add(url)

        html = fetch_page(url)
        if not html:
            progress.update(1)
            continue

        main_content = extract_main_content(html, url, main_selectors)

        if main_content.strip().startswith("#") and "\n" in main_content:
            # trafilatura may already return markdown
            markdown = main_content
        else:
            markdown = html_fragment_to_markdown(main_content)

        markdown = clean_markdown(markdown)

        if markdown and len(markdown.split()) > 40:
            file_path = save_markdown(output_dir, url, markdown)
            save_metadata(output_dir, url, file_path)

        links = extract_links(html, url)
        for link in links:
            if link not in visited and allowed_url(link, allowed_prefixes):
                queue.append(link)

        time.sleep(CRAWL_DELAY)
        progress.update(1)

    progress.close()
    print(f"Saved crawled docs to: {output_dir}")
    print(f"Pages visited: {len(visited)}")


def main() -> None:
    for site in SITES:
        crawl_site(site)


if __name__ == "__main__":
    main()