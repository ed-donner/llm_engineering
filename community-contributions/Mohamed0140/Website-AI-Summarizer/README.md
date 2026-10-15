# Website AI Summarizer

A Python application that fetches the content of a website, 
generates an AI-powered summary using the OpenAI API, and exports the result as a PDF.

## Features

- Scrapes and cleans website content
- Generates concise AI summaries
- Exports summaries as PDF
- Modular Python project structure

## Technologies

- Python
- OpenAI API
- BeautifulSoup
- Requests
- FPDF
- uv

## Installation

uv sync

Create a `.env` file:

```env
OPENAI_API_KEY=your_api_key
```

Run the project:

uv run pdf_generator.py

## Future Improvements

- TXT export
- DOCX export
- Streamlit web interface
- Support for additional content sources