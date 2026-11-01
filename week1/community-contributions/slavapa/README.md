# Week 1 Day 1 — Playwright Web Scraper Exercise

Playwright-enhanced scraper for JavaScript-rendered sites.

**Sites tested:** kabbalahmedia.info, michaellaitman.com, kabuconnect.com

## Setup

```bash
uv pip install playwright
python -m playwright install chromium
```

Or: `uv pip install -r requirements.txt && python -m playwright install chromium`

## Files

- `scraper_playwright.py` — drop-in replacement for `week1/scraper.py` with Playwright fallback
- `day1_playwright_exercise.ipynb` — summarizer demo using the three exercise sites

## Usage in a notebook

```python
from scraper_playwright import fetch_website_contents
content = fetch_website_contents("https://kabbalahmedia.info/en/")
```
