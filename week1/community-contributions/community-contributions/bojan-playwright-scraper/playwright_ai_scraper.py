# playwright_ai_scraper.py
import asyncio
import logging
import random
import time
import os
from playwright.async_api import async_playwright
from openai import OpenAI
from prometheus_client import Counter, Histogram, start_http_server
from diskcache import Cache
from dotenv import load_dotenv

# Loading .env variablesi
load_dotenv()

# Setting up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Setting up Prometheus metrics
SCRAPE_ATTEMPTS = Counter("scrape_attempts", "Total scraping attempts")
SCRAPE_DURATION = Histogram(
    "scrape_duration", "Scraping duration distribution"
)

# Setting up cache
cache = Cache("./scraper_cache")

# Custom exceptions


class ScrapingError(Exception):
    pass


class AnalysisError(Exception):
    pass


class AIScraper:
    API_KEY = os.getenv("OPENAI_API_KEY")
    MAX_CONTENT = int(os.getenv("MAX_CONTENT_LENGTH", 30000))

    def __init__(self, headless=True):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 "
            "Safari/537.36"
        ]
        self.timeout = 60000  # 60 seconds
        self.retries = int(os.getenv("RETRY_COUNT", 2))
        self.headless = headless
        self.delays = {
            "scroll": (500, 2000),
            "click": (100, 300),
            "move": (50, 200)
        }

    async def human_interaction(self, page):
        """Simulates human behavior on the page."""
        try:
            for _ in range(random.randint(2, 5)):
                x = random.randint(0, 1366)
                y = random.randint(0, 768)
                await page.mouse.move(x, y, steps=random.randint(5, 20))
                await page.wait_for_timeout(
                    random.randint(*self.delays["move"])
                )
            scroll = random.choice([300, 600, 900])
            await page.mouse.wheel(0, scroll)
            await page.wait_for_timeout(
                random.randint(*self.delays["scroll"])
            )
        except Exception as e:
            logging.warning(f"Human interaction failed: {e}")

    async def load_page(self, page, url):
        """Loads the page with dynamic waiting."""
        start_time = time.time()
        try:
            await page.goto(
                url, wait_until="domcontentloaded", timeout=self.timeout
            )
            selectors = [
                "main article",
                "#main-content",
                "section:first-of-type",
                'div[class*="content"]',
                "body"
            ]
            for selector in selectors:
                element = await page.query_selector(selector)
                if element:
                    return True
            if time.time() - start_time < 30:
                await page.wait_for_timeout(
                    30000 - int(time.time() - start_time)
                )
            return True
        except Exception as e:
            logging.error(f"Error loading {url}: {e}")
            return False

    async def scrape_with_retry(self, url):
        """Scrapes the page with retries."""
        SCRAPE_ATTEMPTS.inc()
        start_time = time.time()
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(
                    user_agent=random.choice(self.user_agents),
                    viewport={"width": 1366, "height": 768}
                )
                page = await context.new_page()
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => false
                    });
                """)
                for attempt in range(self.retries):
                    try:
                        logging.info(
                            f"Attempt {attempt + 1}: Scraping {url}")
                        if not await self.load_page(page, url):
                            raise ScrapingError(f"Failed to load {url}")
                        await self.human_interaction(page)
                        content = await page.evaluate(
                            """() => {
                                const s = [
                                    'main article',
                                    '#main-content',
                                    'section:first-of-type',
                                    'div[class*="content"]'
                                ];
                                let c = '';
                                for (const x of s) {
                                    const e = document.querySelector(x);
                                    if (e) c += e.innerText + '\\n';
                                }
                                return c.trim() || document.body.innerText;
                            }"""
                        )
                        if not content.strip():
                            raise ScrapingError("No content")
                        SCRAPE_DURATION.observe(time.time() - start_time)
                        return content[:self.MAX_CONTENT]
                    except ScrapingError as e:
                        logging.warning(f"Attempt {attempt + 1} failed: {e}")
                        if attempt < self.retries - 1:
                            await asyncio.sleep(5)
                        else:
                            raise
            except Exception as e:
                logging.error(f"Error in scrape: {e}")
                raise
            finally:
                await browser.close()
        raise ScrapingError(f"All attempts to scrape {url} failed")

    async def get_cached_content(self, url):
        """Retrieves content from cache or scrapes."""
        key = f"content_{url.replace('/', '_')}"
        content = cache.get(key)
        if content is None:
            try:
                content = await self.scrape_with_retry(url)
                cache.set(
                    key, content, expire=int(os.getenv("CACHE_EXPIRY", 3600))
                )
            except Exception as e:
                logging.error(f"Err: {e}")
                raise
        return content


async def analyze_content(url, headless=True):
    """Analyzes the page content using the OpenAI API."""
    try:
        scraper = AIScraper(headless=headless)
        content = await scraper.get_cached_content(url)
        client = OpenAI(api_key=scraper.API_KEY)
        if not client.api_key:
            raise AnalysisError("OpenAI API key not configured")
        prompt = """
            Analyze the website content and extract:
            1. **Summary**: Overview of the website's purpose.
            2. **Entities**: Prominent individuals or organizations.
            3. **Updates**: Recent announcements or news.
            4. **Topics**: Primary subjects or themes.
            5. **Features**: Noteworthy projects or initiatives.
            Format output under these headings. Note if info is missing.
            Content: {content}
        """.format(content=content)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4-turbo"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=float(os.getenv("MODEL_TEMPERATURE", 0.3)),
            max_tokens=int(os.getenv("MAX_TOKENS", 1500)),
            top_p=float(os.getenv("MODEL_TOP_P", 0.9))
        )
        if not response.choices:
            raise AnalysisError("Empty response from OpenAI")
        return response.choices[0].message.content
    except (ScrapingError, AnalysisError) as e:
        logging.error(f"Analysis failed: {e}")
        return f"Error: {e}"
    except Exception as e:
        logging.exception(f"Error in analyze: {e}")
        return f"Unexpected error: {e}"


async def main():
    """Main function for scraping and analysis."""
    try:
        port = int(os.getenv("PROMETHEUS_PORT", 8000))
        start_http_server(port)
        logging.info(f"Prometheus server started on port {port}")
    except Exception as e:
        logging.warning(f"Prometheus server failed: {e}")
    urls = [
        "https://www.anthropic.com",
        "https://deepmind.google",
        "https://huggingface.co",
        "https://runwayml.com"
    ]
    for url in urls:
        start_time = time.time()
        result = await analyze_content(url, headless=True)
        end_time = time.time()
        print(
            f"\nAnalysis of {url} completed in "
            f"{end_time - start_time:.2f} seconds\n"
        )
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
