# CodingForEternity — Week 1

This folder contains my completed Week 1 exercises and experiments from the LLM Engineering course.

## Contents

- `week1-day1.ipynb` — OpenAI and Ollama calls, webpage summarization, and an email subject-line generator.
- `week1-day2.ipynb` — OpenAI-compatible endpoints with OpenAI, Gemini, Ollama, and DeepSeek.
- `week1-exercise.ipynb` — A streaming technical tutor that compares OpenAI, Llama 3.2, and Qwen.
- `week1-day1-web-scraper.ipynb` — A Selenium-based scraper for JavaScript-rendered websites with optional LLM summarization.
- `scraper.py` — The course scraper helper used by the notebooks.

## Setup

Install the repository dependencies as described in the root README. The Selenium notebook additionally requires:

```bash
pip install -r week1/community-contributions/codingforeternity/requirements.txt
```

Add provider credentials such as `OPENAI_API_KEY` or `GOOGLE_API_KEY` to the repository `.env` file. For the local examples, install Ollama and pull the models referenced in the notebooks.

Notebook outputs have been cleared intentionally before submission.
