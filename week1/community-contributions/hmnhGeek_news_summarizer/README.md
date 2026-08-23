# News Summarizer using OpenAI API

This project is a lightweight **news summarization tool** that takes a news article URL, extracts its content, and uses the Chat Completions API to generate a structured summary in markdown format.

It is designed to run in a Jupyter Notebook or any Python environment that supports IPython display.

---

## What it does

Given a news article URL, the program:

1. Scrapes the full text content from the webpage
2. Sends the extracted text to a language model via the OpenAI-compatible API
3. Uses a carefully designed system prompt to:
   - Summarize the article in **simple language**
   - Keep the summary within **3 short paragraphs**
   - Ignore navigation or irrelevant website text
   - Detect if the content is not actually a news article
   - Classify sentiment as **positive, negative, or neutral**
   - Extract and list any mentioned characters/entities
4. Displays the final response as **rendered Markdown**

---

## Key Features

- 🔎 Web scraping integration (via `fetch_website_contents`)
- 🤖 AI-powered summarization using configurable LLM backend
- 🧠 Intelligent filtering of non-news content
- 📊 Sentiment tagging (positive / negative / neutral)
- 👥 Named entity extraction (characters involved)
- 📄 Clean Markdown output rendering in Jupyter

---
