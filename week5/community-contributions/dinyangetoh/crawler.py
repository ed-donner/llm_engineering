"""
Domain-scoped website crawler using requests + BeautifulSoup.
Ignores external links; returns pages with source URL and crawl stats.
"""
from __future__ import annotations

import queue
import threading
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT}
DEFAULT_DELAY = 0.5


def _normalize_url(url: str, base: str) -> str:
    full = urljoin(base, url)
    parsed = urlparse(full)
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def _same_domain(url: str, seed_netloc: str) -> bool:
    parsed = urlparse(url)
    if not parsed.netloc or not parsed.scheme.startswith("http"):
        return False
    return parsed.netloc.lower() == seed_netloc.lower()


def _extract_text(soup: BeautifulSoup) -> str:
    if soup.body:
        for tag in soup.body(["script", "style", "nav", "header", "footer", "img", "input"]):
            tag.decompose()
        return soup.body.get_text(separator="\n", strip=True)
    return ""


def _get_links(soup: BeautifulSoup, base_url: str, seed_netloc: str) -> set[str]:
    out = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        full = _normalize_url(href, base_url)
        if _same_domain(full, seed_netloc):
            out.add(full)
    return out


def _fetch_page(url: str) -> tuple[BeautifulSoup, str, str] | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "html.parser")
        title = (soup.title.string or "").strip() if soup.title else "No title"
        text = _extract_text(soup)
        return (soup, title, text)
    except Exception:
        return None


def _crawl_concurrent(
    base_url: str,
    max_links: int,
    delay: float,
    workers: int,
    verbose: bool,
    progress_callback: Callable[[int, int, int], None] | None = None,
) -> tuple[list[dict], dict]:
    parsed = urlparse(base_url)
    if not parsed.scheme or not parsed.netloc:
        base_url = urljoin("https://", base_url)
    parsed = urlparse(base_url)
    seed_netloc = parsed.netloc
    seed_url = _normalize_url(base_url, base_url)

    to_visit: queue.Queue[str | None] = queue.Queue()
    to_visit.put(seed_url)
    lock = threading.Lock()
    visited: set[str] = set()
    pages: list[dict] = []
    all_links: set[str] = set()
    active_workers = 0
    rate_lock = threading.Lock()
    last_request_time: list[float] = [0.0]

    def worker() -> None:
        nonlocal active_workers
        while True:
            try:
                url = to_visit.get(timeout=0.5)
            except queue.Empty:
                with lock:
                    if to_visit.empty() and active_workers == 0:
                        for _ in range(workers):
                            to_visit.put(None)
                continue
            if url is None:
                break
            with lock:
                if url in visited:
                    continue
                visited.add(url)
                active_workers += 1

            result = _fetch_page(url)

            with rate_lock:
                now = time.monotonic()
                wait = last_request_time[0] + delay - now
                if wait > 0:
                    time.sleep(wait)
                last_request_time[0] = time.monotonic()

            with lock:
                active_workers -= 1
                if result is None:
                    continue
                soup, title, text = result
                pages.append({"url": url, "title": title, "text": text})
                if verbose and len(pages) > 0 and len(pages) % 5 == 0:
                    print(
                        f"Crawled {len(pages)} / {max_links} (queue: {to_visit.qsize()})", flush=True)
                if progress_callback is not None:
                    progress_callback(len(pages), max_links, to_visit.qsize())
                links = _get_links(soup, url, seed_netloc)
                all_links.update(links)
                if len(pages) >= max_links:
                    for _ in range(workers):
                        to_visit.put(None)
                    continue
                for link in links:
                    if link not in visited:
                        to_visit.put(link)

    threads = [threading.Thread(target=worker) for _ in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    stats = {
        "total_pages_visited": len(pages),
        "total_links_discovered": len(all_links),
        "domain": seed_netloc,
    }
    return pages, stats


def crawl_site(
    base_url: str,
    output_dir: Path | None = None,
    max_links: int = 200,
    delay: float = DEFAULT_DELAY,
    workers: int = 1,
    verbose: bool = True,
    progress_callback: Callable[[int, int, int], None] | None = None,
) -> tuple[list[dict], dict]:
    """
    Crawl a website starting from base_url. Only follows same-domain links.
    Ignores external links. Tracks visited to avoid duplicates.

    Returns:
        (pages, stats): pages is list of {url, title, text}; stats has
        total_pages_visited, total_links_discovered.
    """
    if workers > 1:
        pages, stats = _crawl_concurrent(
            base_url=base_url,
            max_links=max_links,
            delay=delay,
            workers=workers,
            verbose=verbose,
            progress_callback=progress_callback,
        )
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            summary_path = output_dir / "_summary.md"
            summary_path.write_text(
                f"# Crawl summary\n\n"
                f"- Domain: {stats['domain']}\n"
                f"- Crawl date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
                f"- Total pages visited: {stats['total_pages_visited']}\n"
                f"- Total links discovered (same-domain): {stats['total_links_discovered']}\n",
                encoding="utf-8",
            )
        return pages, stats

    parsed = urlparse(base_url)
    if not parsed.scheme or not parsed.netloc:
        base_url = urljoin("https://", base_url)
    parsed = urlparse(base_url)
    seed_netloc = parsed.netloc

    to_visit: list[str] = [_normalize_url(base_url, base_url)]
    visited: set[str] = set()
    all_links: set[str] = set()
    pages: list[dict] = []

    while to_visit and len(visited) < max_links:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        result = _fetch_page(url)
        if result is None:
            continue

        soup, title, text = result
        pages.append({"url": url, "title": title, "text": text})

        if verbose and len(pages) > 0 and len(pages) % 5 == 0:
            print(
                f"Crawled {len(pages)} / {max_links} (queue: {len(to_visit)})", flush=True)
        if progress_callback is not None:
            progress_callback(len(pages), max_links, len(to_visit))

        links = _get_links(soup, url, seed_netloc)
        all_links.update(links)
        for link in links:
            if link not in visited and link not in to_visit:
                to_visit.append(link)

        if delay > 0:
            time.sleep(delay)

    stats = {
        "total_pages_visited": len(pages),
        "total_links_discovered": len(all_links),
        "domain": seed_netloc,
    }

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        summary_path = output_dir / "_summary.md"
        summary_path.write_text(
            f"# Crawl summary\n\n"
            f"- Domain: {stats['domain']}\n"
            f"- Crawl date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"- Total pages visited: {stats['total_pages_visited']}\n"
            f"- Total links discovered (same-domain): {stats['total_links_discovered']}\n",
            encoding="utf-8",
        )

    return pages, stats
