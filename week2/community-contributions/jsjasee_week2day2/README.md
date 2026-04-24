# Recipe Cookbook Generator for Beginners

This project turns a cooking website into a short beginner-friendly cookbook.

The notebook scrapes a recipe site, asks an LLM to choose the 3 easiest recipes for a complete beginner, then generates a concise cookbook in markdown. A small Gradio interface is included so you can run it as an interactive app.

## Project Files

- `recipe_picker.ipynb` - main notebook containing the scraping, prompt design, model calls, and Gradio UI
- `scraper.py` - helper functions for fetching page text and collecting links from a website

## How It Works

1. Load API keys from a `.env` file.
2. Scrape links from a cooking website.
3. Use an LLM to rank the 3 easiest beginner recipes based on:
   - short total time
   - basic equipment only
   - few common ingredients
   - simple cooking techniques
4. Fetch the landing page and selected recipe pages.
5. Ask the model to rewrite the scraped content into a friendly "Beginner's Cookbook".
6. Stream the result into a Gradio app.

## Features

- Scrapes cooking websites with `requests` and `BeautifulSoup`
- Filters recipe links with structured JSON output from an LLM
- Builds a beginner-focused cookbook from scraped content
- Streams responses live in a Gradio interface
- Supports OpenAI-compatible model calls, with setup shown for OpenAI and Google Gemini

## Requirements

Install the Python packages used in the notebook:

```bash
pip install openai python-dotenv gradio beautifulsoup4 requests ipython
```

## Environment Setup

Create a `.env` file with the API keys you want to use:

```env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
```

The notebook currently initializes:

- `OpenAI()` for OpenAI models
- an OpenAI-compatible client for Gemini via Google's OpenAI-style endpoint

Anthropic setup is present in comments and can be enabled if needed.

## Running the Project

Open the notebook:

```bash
jupyter notebook "/Users/tayjiasheng/AI Projects/llm_engineering/week2/community-contributions/jsjasee_week2day2/recipe_picker.ipynb"
```

Run the cells in order. The final section launches a Gradio app where you can:

- enter a recipe or cooking website URL
- choose a model
- generate a markdown cookbook for beginners

Example URLs used in the notebook:

- `https://www.budgetbytes.com/`
- `https://goodcheapeats.com/category/main-dishes/`

## Output

The generated cookbook is designed to include:

- a short confidence-boosting intro for each recipe
- total time and servings
- basic equipment
- ingredients with simple substitutions
- numbered beginner-friendly steps
- one practical beginner tip
- a final recommendation for which recipe to cook first

## Notes

- `scraper.py` truncates page content to 2,000 characters per page.
- The notebook truncates the assembled prompt to 5,000 characters before sending it to the cookbook-generation step.
- Link selection expects JSON output from the model.
- The project is aimed at beginner cooks, so the prompt strongly prefers simple, low-equipment recipes.

## Possible Improvements

- handle relative URLs more robustly
- avoid fetching the same page multiple times
- add error handling for unsupported or blocked websites
- validate the model JSON response before parsing
- export the generated cookbook directly to a markdown file
