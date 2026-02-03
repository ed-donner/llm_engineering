# Investment Website Qualifier (Day 1)

## Overview

This notebook implements a **lightweight AI-powered investment website qualifier**.

Its purpose is to:
- Scrape the textual content of a stock- or investment-related website
- Feed that content into a large language model
- Generate a **concise, readable, and slightly humorous summary**
- Extract a **high-level qualitative assessment of listed stocks**, including:
  - Performance classification
  - Volatility estimate

This tool is intended for **early-stage screening and exploration**, not for trading or financial advice.

---

## What the Notebook Does

At a high level, the notebook performs the following steps:

### 1. Environment Setup
- Loads environment variables using `python-dotenv`
- Reads the OpenAI API key from a `.env` file
- Performs basic validation to ensure the key is present and properly formatted

### 2. Website Scraping
- Uses a helper function (`fetch_website_contents`) from a custom `scraper` module
- Retrieves readable text from the target website
- Ignores layout, navigation, and non-essential markup

### 3. Prompt Construction
- Defines a **system prompt** that enforces:
  - Markdown output
  - Clear structure
  - Concise language with light humor
- Defines a **user prompt** requesting:
  - A short summary of the website
  - A table of stocks with performance and volatility labels
  - A summary of notable news or announcements (if present)

### 4. LLM Invocation
- Sends the scraped website content to the OpenAI Chat Completion API
- Requests a structured Markdown response

### 5. Output Rendering
- Displays the model output directly in the notebook
- Uses Markdown rendering for clean readability

---

## Output Format

The notebook produces **Markdown-formatted output** containing:

- A short natural-language summary of the website
- A table with the following columns:
  - **Stock Name**
  - **Performance** (`Good`, `Bad`, or `Neutral`)
  - **Volatility** (`High`, `Mid`, or `Low`)
- A brief summary of any recent or notable announcements found on the site

This format makes the results easy to:
- Read directly in Jupyter
- Export to documentation
- Feed into downstream analysis pipelines

---

## Intended Use Case

This notebook is designed for:
- Early-stage investment research
- Rapid qualification of unfamiliar investment platforms
- Experimentation with:
  - Web scraping
  - Prompt engineering
  - LLM-assisted qualitative analysis

It is **not intended** to:
- Provide financial advice
- Replace quantitative financial data
- Make automated trading decisions

---

## Dependencies

The notebook requires:

- Python 3.9+
- `python-dotenv`
- `openai`
- `IPython`
- A custom `scraper` module exposing:

```python
fetch_website_contents(url: str) -> str
