"""
Drop-in replacement for week1/scraper.py that also handles JavaScript-rendered websites.

fetch_website_contents(url) and fetch_website_links(url) keep the same signatures as scraper.py.
Each call first tries a fast static fetch with requests. If the HTML looks like a JavaScript shell
(very little text, an empty React/Next/Vue mount point, "please enable JavaScript", or a 403/429/503
block), the page is rendered in headless Chromium with Playwright instead.

Setup (once): pip install playwright  (or: uv pip install playwright)
              python -m playwright install chromium
"""

import asyncio
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}

MAX_CHARS = 5_000  # scraper.py uses 2,000; rendered pages tend to carry more useful text
MIN_STATIC_TEXT_CHARS = 600  # less static text than this suggests a JavaScript-rendered page
PAGE_TIMEOUT_SECONDS = 45
SCROLL_STEPS = 6  # scrolls to trigger lazy-loaded / infinite-scroll content

BLOCKED_STATUS_CODES = {401, 403, 406, 429, 503}
BOILERPLATE_TAGS = ["script", "style", "noscript", "template", "svg", "img", "picture", "video", "audio",
                    "iframe", "canvas", "input", "button", "select", "form", "nav", "footer", "header", "aside"]
BOILERPLATE_CLASSES = re.compile(r"cookie|consent|gdpr|newsletter|popup|modal|advert", re.I)
JS_REQUIRED = re.compile(
    r"(enable|turn on|requires?|need)\s+(your\s+)?javascript|javascript\s+(is\s+)?(required|disabled|not enabled)",
    re.I,
)
SPA_MOUNT_POINTS = ["#root", "#app", "#__next", "#__nuxt", "#___gatsby", "[ng-app]", "app-root", "[data-reactroot]"]
COOKIE_BUTTON = re.compile(r"^\s*(accept|agree|allow|i agree|got it|ok|okay|continue)\b", re.I)

# page.content() does not include open shadow DOM (web components); this walks it as well
DEEP_TEXT_SCRIPT = """
() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'SVG']);
  const parts = [];
  const walk = (node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      const t = node.textContent.trim();
      if (t) parts.push(t);
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE && node.nodeType !== Node.DOCUMENT_FRAGMENT_NODE) return;
    if (node.tagName && skip.has(node.tagName)) return;
    if (node.shadowRoot) walk(node.shadowRoot);
    for (const child of node.childNodes) walk(child);
  };
  walk(document.body || document.documentElement);
  return parts.join('\\n');
}
"""


@dataclass
class Page:
    url: str
    title: str
    description: str
    text: str
    links: list
    method: str  # "static" or "browser"
    notes: list = field(default_factory=list)

    def contents(self, max_chars=MAX_CHARS):
        parts = [self.title]
        if self.description and self.description not in self.text:
            parts.append(self.description)
        parts.append(self.text)
        return "\n\n".join(part for part in parts if part)[:max_chars]


# ---------- HTML cleaning (shared by the static and browser paths) ----------

def _dedupe_lines(text):
    seen, lines = set(), []
    for line in (line.strip() for line in text.splitlines()):
        if line and line.lower() not in seen:
            seen.add(line.lower())
            lines.append(line)
    return "\n".join(lines)


def _extract_links(soup, base_url):
    links = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href and not href.startswith(("#", "javascript:", "mailto:", "tel:")):
            absolute = urljoin(base_url, href)
            if absolute not in links:
                links.append(absolute)
    return links


def parse_html(html, base_url):
    """Return (title, description, readable_text, links) from raw or rendered HTML."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    meta = {}
    for tag in soup.find_all("meta", content=True):
        key = tag.get("name") or tag.get("property")
        if key:
            meta[key.lower()] = tag["content"].strip()
    title = title or meta.get("og:title", "No title found")
    description = meta.get("description") or meta.get("og:description", "")
    links = _extract_links(soup, base_url)

    root = soup.body or soup
    for tag in root(BOILERPLATE_TAGS):
        tag.decompose()
    for tag in root.select('[role="navigation"], [role="banner"], [role="contentinfo"], [aria-hidden="true"]'):
        tag.decompose()
    for tag in root.find_all(True):
        if tag.decomposed or tag.attrs is None or tag.name in {"body", "main", "article"}:
            continue
        marker = " ".join([tag.get("id") or "", *(tag.get("class") or [])])
        if marker.strip() and BOILERPLATE_CLASSES.search(marker):
            tag.decompose()

    text = _dedupe_lines(root.get_text(separator="\n", strip=True))
    main = root.find("main") or root.find("article") or root.find(attrs={"role": "main"})
    if main:
        main_text = _dedupe_lines(main.get_text(separator="\n", strip=True))
        if len(main_text) >= 200 and len(main_text) >= 0.4 * len(text):
            text = main_text
    return title, description, text, links


def needs_browser(html, text):
    """Reasons the static HTML looks like a JavaScript shell; an empty list means it is fine."""
    reasons = []
    if len(text) < MIN_STATIC_TEXT_CHARS:
        reasons.append(f"only {len(text)} characters of static text")
    soup = BeautifulSoup(html, "html.parser")
    noscript = " ".join(tag.get_text(" ", strip=True) for tag in soup.find_all("noscript"))
    if JS_REQUIRED.search(noscript) or JS_REQUIRED.search(text[:2_000]):
        reasons.append("page says JavaScript is required")
    for selector in SPA_MOUNT_POINTS:
        mount = soup.select_one(selector)
        if mount is not None and len(mount.get_text(strip=True)) < 200:
            reasons.append(f"empty single-page-app mount point ({selector})")
            break
    scripts = len(soup.find_all("script"))
    if scripts >= 15 and len(text) < 3 * MIN_STATIC_TEXT_CHARS:
        reasons.append(f"{scripts} scripts but little text")
    return reasons


# ---------- Headless browser ----------

def _dismiss_cookie_banner(page):
    for frame in page.frames[:5]:  # consent dialogs often live in an iframe
        try:
            button = frame.get_by_role("button", name=COOKIE_BUTTON).first
            if button.is_visible(timeout=500):
                button.click(timeout=1_500)
                page.wait_for_timeout(500)
                return True
        except Exception:
            continue
    return False


def _render(url, timeout_seconds, scroll_steps):
    # Playwright launches Chromium as a subprocess, which on Windows needs the Proactor event loop
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    try:
        from playwright.sync_api import Error as PlaywrightError, TimeoutError as PlaywrightTimeout, sync_playwright
    except ImportError as error:
        raise RuntimeError("Playwright is not installed: pip install playwright") from error

    timeout_ms = int(timeout_seconds * 1_000)
    notes = []
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except PlaywrightError as error:
            raise RuntimeError("Chromium is missing: python -m playwright install chromium") from error
        try:
            context = browser.new_context(user_agent=USER_AGENT, locale="en-US", viewport={"width": 1366, "height": 900})
            # images, video and fonts are not needed for text and slow the page down
            context.route("**/*", lambda route: route.abort()
                          if route.request.resource_type in {"image", "media", "font"} else route.continue_())
            page = context.new_page()
            response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            if response is not None and response.status >= 400:
                notes.append(f"browser received HTTP {response.status}")
            try:
                page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 15_000))
            except PlaywrightTimeout:
                notes.append("network never went idle; used the content loaded so far")
            if _dismiss_cookie_banner(page):
                notes.append("dismissed a cookie banner")
            for _ in range(max(0, scroll_steps)):
                page.mouse.wheel(0, 2_500)
                page.wait_for_timeout(400)
            try:
                page.wait_for_load_state("networkidle", timeout=3_000)
            except PlaywrightTimeout:
                pass
            return page.content(), page.evaluate(DEEP_TEXT_SCRIPT), page.url, notes
        finally:
            browser.close()


def render_page(url, timeout_seconds=PAGE_TIMEOUT_SECONDS, scroll_steps=SCROLL_STEPS):
    """Render in a worker thread: Playwright's sync API cannot run inside Jupyter's event loop."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(_render, url, timeout_seconds, scroll_steps).result()


# ---------- Public API ----------

def fetch_page(url, mode="auto", verbose=False):
    """
    Fetch a page and return a Page.
    mode="auto": static first, headless browser only if needed (default)
    mode="static": requests only, no browser (stricter cleaning than scraper.py; raises on HTTP errors)
    mode="browser": always render with the headless browser
    """
    if mode not in {"auto", "static", "browser"}:
        raise ValueError("mode must be 'auto', 'static' or 'browser'")
    if not urlsplit(url).scheme:
        url = "https://" + url
    static_page, reasons = None, []

    if mode != "browser":
        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            title, description, text, links = parse_html(response.text, response.url)
            static_page = Page(response.url, title, description, text, links, "static")
            reasons = needs_browser(response.text, text)
        except requests.HTTPError as error:
            status = error.response.status_code if error.response is not None else None
            if mode == "static" or status not in BLOCKED_STATUS_CODES:
                raise
            reasons = [f"static request blocked (HTTP {status})"]
        except requests.RequestException as error:
            if mode == "static":
                raise
            reasons = [f"static request failed ({type(error).__name__})"]
        if mode == "static" or not reasons:
            if verbose:
                print(f"[static] {len(static_page.text):,} characters from {url}")
            return static_page
        if verbose:
            print(f"[auto] using headless browser because: {'; '.join(reasons)}")

    try:
        html, deep_text, final_url, notes = render_page(url)
    except Exception as error:
        if static_page is None:
            raise
        static_page.notes.append(f"browser failed ({type(error).__name__}); used static HTML")
        return static_page

    title, description, text, links = parse_html(html, final_url)
    deep_text = _dedupe_lines(deep_text)
    if len(deep_text) > 2 * max(len(text), 1):
        text = deep_text
        notes.append("used full DOM text including shadow DOM; cleaned text was much shorter")
    page = Page(final_url, title, description, text, links, "browser", notes)
    if static_page is not None and len(static_page.text) > len(page.text):
        page = static_page  # rendering did not add anything
    if verbose:
        extra = f" ({'; '.join(page.notes)})" if page.notes else ""
        print(f"[{page.method}] {len(page.text):,} characters from {url}{extra}")
    return page


def fetch_website_contents(url, mode="auto", max_chars=MAX_CHARS):
    """Return the title and contents of the website at the given url, rendering JavaScript when needed."""
    return fetch_page(url, mode).contents(max_chars)


def fetch_website_links(url, mode="auto"):
    """Return the absolute links on the website at the given url, including JavaScript-generated ones."""
    return fetch_page(url, mode).links
