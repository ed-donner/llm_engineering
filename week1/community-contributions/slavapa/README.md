# slavapa — Week 1 community contributions

Playwright-enhanced scraper plus Day 1 / Day 2 website summarizer exercises.

**Sites tested:** kabbalahmedia.info, michaellaitman.com, kabuconnect.com

## Setup

```bash
uv pip install playwright
python -m playwright install chromium
```

Or: `uv pip install -r requirements.txt && python -m playwright install chromium`

For Day 2 (Ollama): install from [ollama.com](https://ollama.com), then:

```bash
ollama pull llama3.2
```

Confirm [http://localhost:11434/](http://localhost:11434/) shows `Ollama is running`.

## Files

- `scraper_playwright.py` — drop-in replacement for `week1/scraper.py` with Playwright fallback (cookie dismiss, JS SPA support)
- `day1_email_subject.ipynb` — Day 1 exercise: suggest email subject lines from a draft body
- `day1_playwright_exercise.ipynb` — Day 1 summarizer demo with Playwright + OpenAI
- `day2_ollama_summarizer.ipynb` — Day 2 homework: same summarizer via local Ollama (`llama3.2`)
- `requirements.txt` — Playwright dependency

## Usage in a notebook

```python
from scraper_playwright import fetch_website_contents
content = fetch_website_contents("https://kabbalahmedia.info/en/")
```
