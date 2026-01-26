"""
Queer Currents Digest (QCD) - Automated LGBTQIA+ News Aggregator

This script creates an automated daily digest by scraping prominent LGBTQIA+ news 
outlets and using AI to curate the most critical stories.

Workflow:
1.  **Extract**: Concurrently fetches HTML content from a defined list of URLs 
    using headless Selenium (Chrome) to handle dynamic JavaScript content.
2.  **Transform**: Cleans the raw HTML using BeautifulSoup to remove ads, 
    navigation, and boilerplate text.
3.  **Analyze**: Sends cleaned text to OpenAI (GPT-4o-mini) to generate 
    individual summaries (Top 3 stories) for each source.
4.  **Synthesize**: Aggregates all source summaries and prompts the AI to act 
    as a Lead Editor, selecting and writing a digest for the single most 
    important story of the moment.

Key Features:
- Asynchronous concurrency via `asyncio` and `ThreadPoolExecutor`.
- Robust error handling with silenced Selenium logs for a clean CLI experience.
- centralized OpenAI configuration using `gpt-4o-mini`.

Usage:
    Ensure OPENAI_API_KEY is set in your .env file.
    Run via: python week1_day1_queer_currents_digest.py
"""

import os
import sys
import asyncio
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Optional

# Third-party libraries
from dotenv import load_dotenv
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service 
from bs4 import BeautifulSoup
from tqdm import tqdm

# --- Configuration ---
PROJECT_NAME = "QUEER CURRENTS DIGEST (QCD)"
MODEL_NAME = "gpt-4o-mini"
MAX_WORKERS = 5 

URL_LIST = [
    "https://www.advocate.com",
    "https://www.thepinknews.com",
    "https://www.lgbtqnation.com",
    "https://www.queerty.com",
    "https://www.washingtonblade.com",
    "https://www.out.com",
    "https://www.autostraddle.com",
    "https://www.them.us",
    "https://www.gaytimes.co.uk",
    "https://www.outsports.com",
]

# --- Prompts ---
SYSTEM_PROMPT_SITE = """
You are a news assistant. Analyze the text.
Identify the top 3 most relevant LGBTQIA+ news/topics.
Ignore navigation/ads.
Output strictly a Markdown list with a short, neutral summary.
Format:
- [Topic Name]: [Summary]
"""

USER_PROMPT_SITE_PREFIX = """
Analyze this website content and list the Top 3 most important news items.
Content:
"""

SYSTEM_PROMPT_FINAL = """
You are a lead editor. Review the provided summaries.
Select the SINGLE most important topic across all sources.
Output strictly in Markdown:
### MOST IMPORTANT STORY
**[Title]**
[A detailed paragraph explaining why this is the most critical story right now.]
"""

# --- Data Structures ---
@dataclass
class SiteResult:
    """Data Transfer Object for processing results."""
    url: str
    summary: str
    success: bool
    error_msg: Optional[str] = None

# --- UI / Logging Service ---
class ConsoleUI:
    """Handles clean, icon-free CLI output."""
    
    @staticmethod
    def print_header(title: str):
        print(f"\n{'-' * 60}")
        print(f"{title.upper()}")
        print(f"{'-' * 60}")

    @staticmethod
    def print_subheader(title: str):
        print(f"\n>> {title.upper()}")

    @staticmethod
    def print_error(msg: str):
        print(f"[ERROR] {msg}", file=sys.stderr)

    @staticmethod
    def print_info(msg: str):
        print(f"[INFO] {msg}")

    @staticmethod
    def print_separator():
        print("-" * 60)

# --- Core Logic Services ---

class ContentFetcher:
    """Responsible solely for retrieving and cleaning HTML content."""
    
    def __init__(self):
        self._options = Options()
        self._options.add_argument("--headless")
        self._options.add_argument("--disable-gpu")
        self._options.add_argument("--no-sandbox")
        self._options.add_argument("--disable-dev-shm-usage")
        self._options.add_argument("--log-level=3") # Suppress Selenium Console Info
        self._options.add_experimental_option('excludeSwitches', ['enable-logging'])

    def fetch(self, url: str) -> str:
        """Fetches URL via Selenium and returns cleaned text."""
        driver = None
        try:
            service = Service(log_output=subprocess.DEVNULL)
            
            driver = webdriver.Chrome(options=self._options, service=service)
            driver.set_page_load_timeout(45) 
            driver.get(url)
            return self._clean_html(driver.page_source)
        except Exception as e:
            # We raise a simple string message, suppressing the stack trace
            error_message = str(e).split("\n")[0] # Only take the first line of the error
            raise RuntimeError(error_message)
        finally:
            if driver:
                driver.quit()

    def _clean_html(self, raw_html: str) -> str:
        """Parses HTML and removes noise."""
        soup = BeautifulSoup(raw_html, 'html.parser')
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        
        text = soup.get_text(separator=' ')
        return " ".join(text.split())

class NewsAnalyzer:
    """Responsible for interacting with the AI Model."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def summarize_site(self, content: str) -> str:
        try:
            safe_content = content[:15000] 
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_SITE},
                    {"role": "user", "content": f"{USER_PROMPT_SITE_PREFIX}\n\n{safe_content}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"AI Generation Error: {str(e)}")

    def generate_digest(self, all_summaries: str) -> str:
        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_FINAL},
                {"role": "user", "content": f"Summaries:\n{all_summaries}"}
            ]
        )
        return response.choices[0].message.content

# --- Orchestrator ---

def process_site_task(url: str, api_key: str) -> SiteResult:
    """Synchronous worker function."""
    fetcher = ContentFetcher()
    
    # 1. Fetch
    try:
        content = fetcher.fetch(url)
        if len(content) < 500:
            return SiteResult(url, "", False, "Content too short/empty")
    except Exception as e:
        # e is already cleaned up in fetcher
        return SiteResult(url, "", False, str(e))

    # 2. Analyze
    try:
        analyzer = NewsAnalyzer(api_key)
        summary = analyzer.summarize_site(content)
        return SiteResult(url, summary, True)
    except Exception as e:
        return SiteResult(url, "", False, str(e))

async def run_digest_process():
    """Main Async Controller."""
    
    # 1. Initialization
    ConsoleUI.print_header(PROJECT_NAME)
    load_dotenv(override=True)
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        ConsoleUI.print_error("Missing OPENAI_API_KEY in environment.")
        sys.exit(1)
        
    ConsoleUI.print_info(f"Target URLs: {len(URL_LIST)}")
    ConsoleUI.print_info(f"AI Model: {MODEL_NAME}")
    
    # 2. Concurrent Processing
    ConsoleUI.print_subheader("Phase 1: Scanning & Summarizing Sources")
    
    loop = asyncio.get_running_loop()
    results: List[SiteResult] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            loop.run_in_executor(executor, process_site_task, url, api_key)
            for url in URL_LIST
        ]
        
        for future in tqdm(asyncio.as_completed(futures), total=len(futures), unit="site", desc="Processing"):
            results.append(await future)

    # 3. Aggregation
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    ConsoleUI.print_info(f"Successfully processed: {len(successful)}")
    
    # Clean error reporting without stack traces
    if failed:
        ConsoleUI.print_info(f"Failed Sources: {len(failed)}")
        for f in failed:
            # We strip the "RuntimeError: " prefix if it exists for cleaner output
            clean_msg = f.error_msg.replace("RuntimeError: ", "")
            print(f"  - {f.url}: {clean_msg}")

    if not successful:
        ConsoleUI.print_error("No content fetched. Exiting.")
        return

    # 4. Final Digest
    ConsoleUI.print_subheader("Phase 2: Generating Editorial Digest")
    
    combined_text = "\n".join([f"Source: {r.url}\n{r.summary}\n" for r in successful])
    
    try:
        final_analyzer = NewsAnalyzer(api_key)
        final_digest = final_analyzer.generate_digest(combined_text)
        
        # Only printing the Final Report as requested
        ConsoleUI.print_header("FINAL REPORT")
        print(final_digest)
        ConsoleUI.print_separator()
            
    except Exception as e:
        ConsoleUI.print_error(f"Failed to generate final digest: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_digest_process())
    except KeyboardInterrupt:
        ConsoleUI.print_info("Process interrupted by user.")
        sys.exit(0)
    except Exception as e:
        ConsoleUI.print_error(f"FATAL ERROR: {e}")
        sys.exit(1)