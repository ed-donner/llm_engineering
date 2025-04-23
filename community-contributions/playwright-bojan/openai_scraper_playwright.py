import asyncio
from playwright.async_api import async_playwright
from openai import OpenAI
import logging
import random
import time
import os
from prometheus_client import start_http_server, Counter, Histogram
from diskcache import Cache
from dotenv import load_dotenv

load_dotenv()

# Setting up Prometheus metrics
SCRAPE_ATTEMPTS = Counter('scrape_attempts', 'Total scraping attempts')
SCRAPE_DURATION = Histogram(
    'scrape_duration', 'Scraping duration distribution')

# Setting up cache
cache = Cache('./scraper_cache')


class ScrapingError(Exception):
    pass


class ContentAnalysisError(Exception):
    pass


class EnhancedOpenAIScraper:
    API_KEY = os.getenv("OPENAI_API_KEY")
    BROWSER_EXECUTABLE = os.getenv(
        "BROWSER_PATH", "/usr/bin/chromium-browser")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 30000))

    def __init__(self, headless=True):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
        self.timeout = 45000  # 45 seconds
        self.retry_count = int(os.getenv("RETRY_COUNT", 2))
        self.headless = headless
        self.mouse_velocity_range = (100, 500)  # px/ms
        self.interaction_delays = {
            'scroll': (int(os.getenv("SCROLL_DELAY_MIN", 500)), int(os.getenv("SCROLL_DELAY_MAX", 2000))),
            'click': (int(os.getenv("CLICK_DELAY_MIN", 100)), int(os.getenv("CLICK_DELAY_MAX", 300))),
            'movement': (int(os.getenv("MOVEMENT_DELAY_MIN", 50)), int(os.getenv("MOVEMENT_DELAY_MAX", 200)))
        }
        self.proxy_servers = [server.strip() for server in os.getenv(
            "PROXY_SERVERS", "").split(',') if server.strip()]

    async def human_interaction(self, page):
        """Advanced simulation of user behavior"""
        # Random mouse movement path
        for _ in range(random.randint(2, 5)):
            x = random.randint(0, 1366)
            y = random.randint(0, 768)
            await page.mouse.move(x, y, steps=random.randint(5, 20))
            await page.wait_for_timeout(random.randint(*self.interaction_delays['movement']))

        # Simulating typing
        if random.random() < 0.3:
            await page.keyboard.press('Tab')
            await page.keyboard.type(' ', delay=random.randint(50, 200))

        # More realistic scrolling
        scroll_distance = random.choice([300, 600, 900])
        await page.mouse.wheel(0, scroll_distance)
        await page.wait_for_timeout(random.randint(*self.interaction_delays['scroll']))

    async def load_page(self, page, url):
        """Smarter page loading with dynamic waiting"""
        start_time = time.time()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)

            # Smarter content extraction selectors
            selectors = [
                'main article',
                '#main-content',
                'section:first-of-type',
                'div[class*="content"]',
                'body'  # Fallback
            ]

            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        return True
                except Exception:
                    continue

            # Fallback if no selector is found within a certain time
            if time.time() - start_time < 30:  # If we haven't used the full timeout
                await page.wait_for_timeout(30000 - int(time.time() - start_time))

            return True  # Page likely loaded
        except Exception as e:
            logging.error(f"Error loading page {url}: {e}")
            return False

    @SCRAPE_DURATION.time()
    async def scrape_with_retry(self):
        """Main function with retry mechanism and browser reuse"""
        SCRAPE_ATTEMPTS.inc()
        last_error = None
        browser = None
        context = None
        page = None

        try:
            async with async_playwright() as p:
                launch_args = {
                    "headless": self.headless,
                    "args": [
                        "--disable-blink-features=AutomationControlled",
                        "--single-process",
                        "--no-sandbox",
                        f"--user-agent={random.choice(self.user_agents)}"
                    ],
                    "executable_path": self.BROWSER_EXECUTABLE
                }
                if self.proxy_servers:
                    proxy_url = random.choice(self.proxy_servers)
                    proxy_config = {"server": proxy_url}
                    proxy_username = os.getenv('PROXY_USER')
                    proxy_password = os.getenv('PROXY_PASS')
                    if proxy_username and proxy_password:
                        proxy_config['username'] = proxy_username
                        proxy_config['password'] = proxy_password
                    launch_args['proxy'] = proxy_config

                browser = await p.chromium.launch(**launch_args)
                context = await browser.new_context(
                    user_agent=random.choice(self.user_agents),
                    viewport={"width": 1366, "height": 768},
                    locale=os.getenv("BROWSER_LOCALE", "en-US")
                )
                await context.route("**/*", lambda route: route.continue_())
                page = await context.new_page()
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', { get: () => false });
                    window.navigator.chrome = { runtime: {}, app: { isInstalled: false } };
                """)

                for attempt in range(self.retry_count):
                    try:
                        logging.info(
                            f"Attempt {attempt + 1}: Loading OpenAI...")
                        if not await self.load_page(page, "https://openai.com"):
                            raise ScrapingError(
                                "Failed to load key content on OpenAI website.")
                        await self.human_interaction(page)
                        await page.screenshot(path=f"openai_debug_{attempt}.png")
                        content = await page.evaluate("""() => {
                            const selectors = [
                                'main article',
                                '#main-content',
                                'section:first-of-type',
                                'div[class*="content"]'
                            ];

                            let content = '';
                            for (const selector of selectors) {
                                const element = document.querySelector(selector);
                                if (element) {
                                    content += element.innerText + '\\n\\n';
                                }
                            }
                            return content.trim() || document.body.innerText;
                        }""")
                        if not content.strip():
                            raise ContentAnalysisError(
                                "No content extracted from the page.")
                        return content[:self.MAX_CONTENT_LENGTH]

                    except (ScrapingError, ContentAnalysisError) as e:
                        last_error = e
                        logging.warning(
                            f"Attempt {attempt + 1} failed: {str(e)}")
                        if attempt < self.retry_count - 1:
                            await asyncio.sleep(5)
                        else:
                            if browser:
                                await browser.close()
                                browser = None
                            raise
                    except Exception as e:
                        last_error = e
                        logging.exception(f"Unexpected error on attempt {
                                          attempt + 1}: {str(e)}")
                        if attempt < self.retry_count - 1:
                            await asyncio.sleep(5)
                        else:
                            if browser:
                                await browser.close()
                                browser = None
                            raise

        except Exception as e:
            last_error = e
        finally:
            if browser:
                await browser.close()

        raise last_error if last_error else Exception(
            "All scraping attempts failed.")

    async def get_cached_content(self):
        key = 'openai_content_cache_key'
        content = cache.get(key)
        if content is None:
            content = await self.scrape_with_retry()
            cache.set(key, content, expire=int(
                os.getenv("CACHE_EXPIRY", 3600)))
        return content


async def analyze_content(headless=True):
    try:
        scraper = EnhancedOpenAIScraper(headless=headless)
        content = await scraper.get_cached_content()

        client = OpenAI(api_key=EnhancedOpenAIScraper.API_KEY)
        if not client.api_key:
            raise ContentAnalysisError(
                "OpenAI API key not configured (check environment variables).")

        prompt_template = """
            Analyze the following website content and extract the following information if present:

            1.  **Overall Summary of the Website:** Provide a concise overview of the website's purpose and the main topics discussed.
            2.  **Key Individuals or Entities:** Identify and briefly describe any prominent individuals, companies, or organizations mentioned.
            3.  **Recent Announcements or Updates:** List any recent announcements, news, or updates found on the website, including dates if available.
            4.  **Main Topics or Themes:** Identify the primary subjects or themes explored on the website.
            5.  **Any Noteworthy Features or Projects:** Highlight any significant features, projects, or initiatives mentioned.

            Format the output clearly under each of these headings. If a particular piece of information is not found, indicate that it is not present.

            Content:
            {content}
        """

        formatted_prompt = prompt_template.format(content=content)
        model_name = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
        temperature = float(os.getenv("MODEL_TEMPERATURE", 0.3))
        max_tokens = int(os.getenv("MAX_TOKENS", 1500))
        top_p = float(os.getenv("MODEL_TOP_P", 0.9))

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes website content and extracts key information in a structured format."},
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )

        if not response.choices:
            raise ContentAnalysisError("Empty response from GPT.")

        return response.choices[0].message.content

    except (ScrapingError, ContentAnalysisError) as e:
        logging.error(f"Analysis failed: {str(e)}")
        return f"Critical analysis error: {str(e)}"
    except Exception as e:
        logging.exception("Unexpected error during analysis.")
        return f"Unexpected analysis error: {str(e)}"


async def main():
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Start Prometheus HTTP server for exposing metrics
    try:
        prometheus_port = int(os.getenv("PROMETHEUS_PORT", 8000))
        start_http_server(prometheus_port)
        logging.info(f"Prometheus metrics server started on port {
                     prometheus_port}")
    except Exception as e:
        logging.warning(f"Failed to start Prometheus metrics server: {e}")

    start_time = time.time()
    result = await analyze_content(headless=True)
    end_time = time.time()

    print(f"\nAnalysis completed in {end_time - start_time:.2f} seconds\n")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
