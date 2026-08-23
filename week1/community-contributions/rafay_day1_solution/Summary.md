# Project Summary: LLM Engineering Day 1 Solution

This document summarizes the functionality of the two main files in this solution directory: `website_content.py` and `day1.ipynb`. Together, they form an interactive workflow that fetches real-world website data and processes it using an LLM to generate humorous summaries.

## 1. `website_content.py` (The Scraper)
This Python script provides a robust web scraping utility powered by `playwright`. It is specifically designed to handle dynamic websites and bypass common environmental issues.

- **Dynamic Content Extraction:** It launches a headless Chromium browser, navigates to the requested URL, and waits for the network to idle. It specifically extracts the visible text on the page (`page.inner_text`).
- **Lazy-Loading Support:** To ensure it captures content that only loads as the user scrolls (common on sites like Airbnb or modern news sites), it executes a JavaScript snippet to scroll the page 8 times, pausing in between.
- **Jupyter Environment Workaround:** Running Playwright natively inside a Jupyter Notebook on Windows often causes `NotImplementedError` due to `asyncio` event loop conflicts. This file cleverly solves this by keeping the Playwright logic entirely synchronous (`_scrape_sync`), and then wrapping it in an asynchronous function (`scrape`) that runs the synchronous code in a separate thread using `asyncio.to_thread()`.

## 2. `day1.ipynb` (The Orchestrator)
This Jupyter Notebook serves as the interactive learning lab. It orchestrates the scraping utility and connects it to the OpenAI API.

- **Environment Verification:** It loads variables from a `.env` file and verifies that the `OPENAI_API_KEY` is formatted correctly, providing troubleshooting tips if it isn't.
- **Prompt Engineering:** It introduces the foundational concept of separating instructions into a `system_prompt` and a `user_prompt`. The notebook configures a system prompt instructing the LLM to act as a "snarky assistant" that provides humorous summaries of websites in Markdown format.
- **The Core Pipeline:** It combines the scraper and the LLM into a seamless workflow. The primary functions (`summarize` and `display_summary`) take a URL, wait for `website_content.py` to scrape the text, format the text into an OpenAI API message payload, and then render the LLM's response directly in the notebook using IPython's `Markdown` display. This provides an end-to-end example of applying generative AI to real-time external data.
