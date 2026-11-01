# run_scraper.py
import asyncio
import sys
from scraper import scrape

url = sys.argv[1]  # ← receives URL from notebook
asyncio.run(scrape(url))