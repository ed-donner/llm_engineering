# Dynamic Web & PDF Content Summarizer

## Overview

This project extracts and summarizes content from modern websites using a smart, multi-stage pipeline.

It supports:
- Static HTML pages
- JavaScript-rendered websites (via Selenium)
- Embedded or linked PDF documents

The extracted content is then summarized using an LLM (OpenAI), with support for large documents through chunking.

---

## Features

### Smart Content Extraction
- Uses `requests` for fast static HTML scraping
- Automatically falls back to Selenium for JavaScript-heavy pages
- Detects sparse content and adapts dynamically

### PDF Detection & Extraction
- Identifies PDFs embedded via:
  - `<a>` links
  - `<iframe>`, `<embed>`, `<object>`
- Extracts text using `pypdf`
- Prioritizes PDF content over webpage wrappers

### Scalable Summarization
- Handles long documents using chunking
- Summarizes each chunk individually
- Combines results into a final summary

---

## Architecture
URL
-> fetch_website_contents()
    -> Static HTML (requests)
    -> Fallback: Selenium (if JS-heavy)
    -> PDF detection across both static HTML and JS pages
-> Raw content (HTML or PDF text)
-> summarize()
    -> Small content -> single LLM call
    -> Large content -> chunk -> summarize -> combine
-> Final summary

---

## Project Structure
teja-dynamic-web-pdf-summarizer/
- seleniumscraperpdfreader.py (content extraction pipeline)
- dynamicwebpdfsummarizer.pynb (LLM summarization logic)
- requirements.txt (dependencies)
- README.md (project documentation)

---

## Key Design Decisions

### Adaptive scraping strategy
Uses Selenium only when necessary to improve performance and reliability

### PDF-first logic
Designed to support embedded pdf content in websites such as reports 

### Separation of concerns
Scraper handles data collection, while summarizer handles LLM processing

### Chunk-based summarization
Prevents token limit issues and enables handling of long documents

---

## Dependencies
Core packages used:
- requests
- beautifulsoup4
- selenium
- webdriver-manager
- pypdf
- openai
- python-dotenv

## Notes and Limitations
- Selenium uses a basic wait approach and could be improved 
- PDF extraction may fail for scanned or image-based pdfs
- Chunking is currently based on character count and could be improved with smarter splitting

## Future Improvements
- Replace simple waits with Selenium explicit waits
- Improve chunking using paragraphs or semantic structure
- Add caching for repeated requests
- Support multiple LLM providers

---

## Author
Teja Chatty

## Acknowledgements
Built as part of the LLM Engineering course by Edward Donner 

