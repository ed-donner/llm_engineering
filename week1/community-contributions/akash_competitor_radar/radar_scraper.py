import os
import sys
import subprocess
import asyncio
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Robust directory path for this module
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_browser_scrape(url: str, headless: bool = False, timeout_ms: int = 30000) -> str:
    """Spawns an independent Chromium instance isolated from Jupyter's event loop."""
    print(f"    🚀 Launching Chromium window for {url}...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            )
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1280, "height": 800},
                ignore_https_errors=True
            )
            page = context.new_page()
            page.add_init_script("delete Object.getPrototypeOf(navigator).webdriver")

            print(f"    🌐 Navigating to {url}...")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            except Exception as e:
                print(f"    ⚠️ Navigation note: {e}")

            page.wait_for_timeout(3000)
            html = page.content()
            browser.close()
            print(f"    ✅ Browser successfully fetched {url}.")

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        cleaned_lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 25]
        extracted_text = "\n".join(cleaned_lines[:150])

        return extracted_text if extracted_text else f"Notice: No text found on {url}"

    except Exception as exc:
        print(f"    ❌ Error during scrape: {exc}")
        return f"Error extracting {url}: {exc}"


def _worker_cli(url: str, headless: bool) -> str:
    """Executes scraping via a clean Python subprocess with a valid Windows working directory."""
    script = f"""
import sys
from radar_scraper import run_browser_scrape
res = run_browser_scrape({repr(url)}, headless={headless})
sys.stdout.buffer.write(res.encode('utf-8', errors='replace'))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        cwd=CURRENT_DIR,  # Always uses the valid folder containing this script
        text=False
    )
    return result.stdout.decode("utf-8", errors="replace")


async def fetch_dynamic_content(url: str, timeout_ms: int = 30000, headless: bool = False) -> str:
    """Non-blocking async wrapper that delegates to the clean subprocess."""
    if not url.startswith("http"):
        url = f"https://{url}"

    return await asyncio.to_thread(_worker_cli, url, headless)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(run_browser_scrape(sys.argv[1]))