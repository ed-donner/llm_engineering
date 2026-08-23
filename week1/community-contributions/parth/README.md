# Pokémon Boss Battle Strategist

A Week 1 Day 1 community contribution that combines web scraping with LLM chat completions to generate battle strategies against Pokémon boss trainers.

## What It Does

Given a trainer name (e.g. Cynthia, Steven Stone), the notebook:

1. Scrapes that trainer's Bulbapedia wiki page for team roster and stat data
2. Sends the scraped content to an LLM with a custom system prompt
3. Returns a markdown-formatted counter-strategy written in the voice of an arrogant rival Champion

The AI persona blends Blue's know-it-all attitude with Silver's disdain for weak opponents. It analyzes type weaknesses, base stats, and vulnerabilities, then spoon-feeds the user an optimal battle plan—while mocking them for needing help in the first place.

## How It Works

```
Trainer name → Bulbapedia URL → scraper.py → LLM (system + user prompts) → Markdown strategy
```

1. **Environment setup** — Loads `OPENAI_API_KEY` from a `.env` file and connects to the GitHub Models inference endpoint (`gpt-4.1-nano`).
2. **Web scraping** — `get_user_message_for_trainer()` formats the trainer name into a Bulbapedia wiki URL and fetches page text via `fetch_website_contents()` from `scraper.py` (truncated to 2,000 characters).
3. **Prompting** — A system prompt defines the arrogant Champion persona and analysis steps. The user message contains the scraped team data and asks for an optimal counter-strategy.
4. **Display** — `display_strategy()` calls the LLM and renders the response as formatted markdown in the notebook.

## Files

| File | Purpose |
|------|---------|
| `day1.ipynb` | Main notebook — setup, prompts, functions, and example runs |
| `scraper.py` | Fetches and cleans website text using `requests` and BeautifulSoup |
| `README.md` | This documentation |

## Requirements

- Python 3.9+
- `python-dotenv`
- `azure-ai-inference`
- `requests`, `beautifulsoup4`
- A valid `OPENAI_API_KEY` in your `.env` file (used with GitHub Models)

## Usage

Run the notebook cells in order, then call:

```python
display_strategy("Cynthia")
display_strategy("Steven_Stone")
```

Use underscores instead of spaces for multi-word trainer names to match Bulbapedia URL conventions.

## Example Trainers

- `Cynthia` — Sinnoh Champion
- `Steven_Stone` — Hoenn Champion
- Any other trainer with a Bulbapedia wiki page
