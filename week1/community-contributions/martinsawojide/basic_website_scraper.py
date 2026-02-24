"""
basic_website_scraper.py -- JS-capable website scraper using undetected Chrome.

Uses undetected-chromedriver to bypass bot-detection on JavaScript-heavy sites,
then extracts the visible text from the fully rendered page.

Dependencies (install via uv from the project root):
    uv add undetected-chromedriver selenium

Usage:
    python week1/community-contributions/basic_website_scraper.py https://example.com
    python week1/community-contributions/basic_website_scraper.py https://openai.com https://anthropic.com
"""

import sys
import time

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def fetch_js_website(url: str, *, headless: bool = True, timeout: int = 30) -> str:
    """
    Scrape the visible text of a JavaScript-rendered webpage.

    Launches a headless Chrome instance via undetected-chromedriver so that
    sites protected by Cloudflare, Akamai, or similar bot-detection don't
    block the request.  The browser fully renders the page (including JS),
    waits for the <body> element, and returns its inner text.

    Args:
        url:      The webpage URL to scrape.
        headless: Run Chrome without a visible window (default True).
        timeout:  Max seconds to wait for the page to load.

    Returns:
        The visible text content of the page body.
    """
    print(f"[1/4] Launching stealth browser...")

    options = uc.ChromeOptions()
    options.page_load_strategy = "eager"
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )

    driver = uc.Chrome(options=options, use_subprocess=False, version_main=144)
    driver.set_page_load_timeout(timeout)
    print("[1/4] Browser launched.")

    try:
        print(f"[2/4] Navigating to {url}")
        start = time.perf_counter()
        try:
            driver.get(url)
        except Exception:
            # Timeout on page load is expected for heavy sites; the body
            # may still be available thanks to the 'eager' load strategy.
            pass
        elapsed = time.perf_counter() - start
        print(f"[2/4] Page response received ({elapsed:.1f}s).")

        print("[3/4] Waiting for page body to render...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("[3/4] DOM ready.")

        print("[4/4] Extracting text content...")
        content = driver.find_element(By.TAG_NAME, "body").text
        print("[4/4] Done.")
    finally:
        driver.quit()

    word_count = len(content.split())
    char_count = len(content)
    print(f"Scraped {url} -- {word_count:,} words, {char_count:,} characters.\n")

    return content


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:  python basic_website_scraper.py <url> [url ...]")
        sys.exit(1)

    for url in sys.argv[1:]:
        print(f"\n--- Scraping: {url} ---")
        text = fetch_js_website(url)
        preview = text[:500] + ("..." if len(text) > 500 else "")
        print(preview)
