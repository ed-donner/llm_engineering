# Lobsters AI Summary

A small Python tool that scrapes the [Lobsters](https://lobste.rs) tech community,
then uses an OpenAI model to produce a concise, witty **Thai-language** summary of
the day's active stories and latest comments.

It pulls two data sources from Lobsters:

1. **Active stories** — titles and links from the [Active](https://lobste.rs/active) page.
2. **Latest comments** — story titles and user comments from the [Comments](https://lobste.rs/comments) page.

The scraped data is fed to `gpt-4.1-mini`, which returns a Markdown summary covering
the main technical themes, interesting engineering discussions, and practical takeaways
for developers. The result is printed to the console and written to `lobsters_summary.md`.

## How it works

```
lobsters_scraper.py   ──>   scrapes Lobsters with Playwright (headless Chromium)
        │
        ▼
lobsters_ai_summary.py ──>   builds a prompt, calls OpenAI, writes lobsters_summary.md
```

| File | Purpose |
| --- | --- |
| `lobsters_ai_summary.py` | Main entry point — scrapes, summarizes, and saves the result. |
| `lobsters_scraper.py` | Playwright scraper for the Active and Comments pages. |
| `tutorial_main.py` | Standalone runner that just prints the scraped data (no AI). |
| `tutorial_playwright.py` | Playwright learning sandbox — not part of the main flow. |

## Requirements

- Python 3.12+
- An [OpenAI API key](https://platform.openai.com/api-keys)

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/KawinYamtuan/llm_project_lobsters_ai_summary.git
cd llm_project_lobsters_ai_summary

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install the Playwright browser (Chromium)
playwright install chromium

# 5. Configure your API key
#    Copy the example file, then edit .env and paste your real key.
cp .env.example .env       # Windows: copy .env.example .env
```

Your `.env` should look like:

```
OPENAI_API_KEY=your_openai_api_key_here
```

> **Note:** `.env` is git-ignored so your key never gets committed.

## Usage

Run the full scrape-and-summarize flow:

```bash
python lobsters_ai_summary.py
```

This prints the summary to the console and saves it to `lobsters_summary.md`.

To see only the raw scraped data (no AI call), run:

```bash
python tutorial_main.py
```

## Notes

- The summary is generated in **Thai** by design (set in the system prompt inside
  `lobsters_ai_summary.py`). Edit the prompt there to change the language or tone.
- The scraper runs headless. Set `headless=False` in `lobsters_scraper.py` if you
  want to watch the browser work.
- This is a learning project from the
  [LLM Engineering course](https://github.com/ed-donner/llm_engineering) (Week 1, Day 1).
