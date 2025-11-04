from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import openai
import json
import re
from difflib import SequenceMatcher
import time


headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36"
    )
}

def pick_main_container(soup):
    candidates = soup.find_all(["main", "article", "section", "div"], recursive=True)
    # Exclude obvious chrome
    bad_ids = ("header", "footer", "nav", "menu")
    bad_roles = ("navigation", "banner", "contentinfo", "complementary")
    best, best_len = soup.body, 0
    for el in candidates:
        rid = (el.get("id") or "").lower()
        role = (el.get("role") or "").lower()
        if any(b in rid for b in bad_ids) or role in bad_roles:
            continue
        txt = el.get_text(" ", strip=True)
        if len(txt) > best_len:
            best, best_len = el, len(txt)
    return best or soup.body


def is_leaf(el):
    # No nested block-level text containers inside
    return not el.find(["p","li","ul","ol","dl","table","section","article","div"])


def is_visible(el):
    if el.has_attr("hidden"): return False
    if el.get("aria-hidden") in ("true", True): return False
    style = (el.get("style") or "").lower()
    if "display:none" in style or "visibility:hidden" in style: return False
    # Also skip elements inside hidden ancestors
    for parent in el.parents:
        if parent and (parent.get("aria-hidden") == "true" or parent.has_attr("hidden")):
            return False
        pstyle = (parent.get("style") or "").lower()
        if "display:none" in pstyle or "visibility:hidden" in pstyle:
            return False
    return True


def norm(txt):
    txt = re.sub(r"\s+", " ", txt).strip()
    txt = re.sub(r"^[•·\-–]*\s*", "", txt)   # strip bullet glyphs
    return txt

def is_dupe(txt, seen, threshold=0.9):
    n = norm(txt).lower()
    for s in seen:
        if SequenceMatcher(None, n, s).ratio() >= threshold:
            return True
    seen.add(n)
    return False

def extract_visible_text(html):
    soup = BeautifulSoup(html, "html.parser")

    # strip obvious chrome globally first
    for t in soup(["script","style","noscript","svg","form","iframe","header","footer","nav","aside"]):
        t.decompose()

    container = pick_main_container(soup)

    blocks = []
    seen = set()

    # Only leaf paragraphs and list items inside main container
    for el in container.find_all(["p","li"], recursive=True):
        if not is_leaf(el):  # skip parents that wrap other blocks
            continue
        if not is_visible(el):
            continue
        txt = el.get_text(" ", strip=True)
        if len(txt.split()) < 3:
            continue
        # light boilerplate filter
        if re.search(r"(cookies|impressum|datenschutz|privacy|subscribe)", txt, re.I):
            continue
        n = norm(txt)
        # fuzzy dedupe to kill near-duplicates
        duplicate = False
        for s in seen:
            if SequenceMatcher(None, n.lower(), s).ratio() >= 0.92:
                duplicate = True
                break
        if not duplicate:
            seen.add(n.lower())
            blocks.append(n)

    # collapse runs of empty lines + keep paragraph spacing
    out = "\n\n".join(blocks)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out



# ---------- PAGE FETCHING (PLAYWRIGHT) ----------

def render_page(url, timeout=40):
    """Render a webpage with Playwright and return the final HTML (sync version)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        ))

        try:
            page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
            time.sleep(5)  # let scripts render dynamic content
            for _ in range(3):
                page.mouse.wheel(0, 1500)
                time.sleep(1)
            html = page.content()
        except Exception as e:
            print(f"⚠️ Playwright error fetching {url}: {e}")
            html = page.content() if page else ""
        finally:
            browser.close()
        return html

# ---------- MAIN ENTRY POINT ----------
def extract_job_description(url):
    print(f"Fetching and cleaning: {url}")
    html = render_page(url)
    text = extract_visible_text(html)
    print(f"Extracted {len(text.split())} words of cleaned text.")
    return text

"""
if __name__ == "__main__":
    url = "https://www.capgemini.com/de-de/jobs/4099909101+greenhousegermaninvent/"
    job_text = extract_job_text(url)
    print("\n--- CLEANED JOB TEXT ---\n")
    print(job_text) """

  