# SafeHire – Week 2 Exercise (winniekariuki)

**SafeHire** is a verification platform for Kenyan domestic workers. This submission is the Week 2 exercise: a QA chat assistant for compliance, red flags, and how to hire a good nanny.

## What's included

- **Gradio UI**: Chat interface with logo, focus (Compliance / Red flags / Hiring), user type (Employer / Worker / Agency), and model switch (GPT-4o-mini, Llama 3.2).
- **Streaming** responses.
- **System prompt** with scraped + curated knowledge (including Kenya minimum wage for domestic workers).
- **Scraping**: Content from configurable URLs (e.g. ILO) plus fallback; optional `search_compliance_knowledge` tool (OpenAI).
- **Chat area** appears only after the first message (ChatGPT-style).

## How to run

1. From repo root, ensure `week2` is on the path (or run the notebook from `week2/community-contributions/winniekariuki/`).
2. Set `OPENAI_API_KEY` (and optionally `GOOGLE_API_KEY`) in `.env`.
3. For Llama: have Ollama running locally.
4. Open `week2 EXERCISE.ipynb`, run all cells. Logo loads from `static/logo.JPG` (or .jpg) if present.

## Dependencies

Uses the course stack: `openai`, `gradio`, `python-dotenv`, `requests`, `beautifulsoup4`. The notebook uses `week2/scraper.py` for fetching compliance URLs.
