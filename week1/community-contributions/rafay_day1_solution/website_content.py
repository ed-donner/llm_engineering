import sys
import asyncio
from playwright.sync_api import sync_playwright

def _scrape_sync(url: str, selector: str = "body"):
    # Fix the event loop policy for the thread running playwright on Windows.
    # This prevents the NotImplementedError when running inside Jupyter Notebooks.
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120 Safari/537.36"
            )
        )

        page = context.new_page()

        try:
            # Load page
            page.goto(url, wait_until="networkidle", timeout=60000)

            # Give extra time for heavy JS
            page.wait_for_timeout(3000)

            # Auto-scroll (important for lazy-loaded sites like Airbnb)
            for _ in range(8):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1500)

            # Wait for content
            page.wait_for_selector(selector, timeout=30000)

            # Extract visible text
            text = page.inner_text(selector)

            return text

        except Exception as e:
            return f"Error: {e}"

        finally:
            browser.close()

async def scrape(url: str, selector: str = "body"):
    """
    Scrapes a website asynchronously, but runs Playwright in a separate thread
    to bypass Jupyter Notebook event loop conflicts on Windows.
    """
    return await asyncio.to_thread(_scrape_sync, url, selector)