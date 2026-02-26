# ebunilo_week_1 – Week 1 community contribution

This folder contains Week 1 notebooks, shared code, and a containerized app for the LLM Engineering course.

## Contents

| Item | Description |
|------|-------------|
| **day1_with_ollama.ipynb** | Day 1 notebook using Ollama (local LLM). |
| **week1 EXERCISE.ipynb** | Week 1 exercise solutions. |
| **scraper.py** | Shared website scraper (links + page content). |
| **app/** | Company Brochure Generator (Day 5 business solution) as a web API, with Docker deployment. |

## Company Brochure Generator (Day 5)

The **app** directory implements the Week 1 Day 5 “full business solution”: a service that builds a company brochure from a name and website URL (scrapes relevant pages, uses an LLM to select links and generate markdown).

- **Run locally:** see [app/README.md](app/README.md) for `pip`/`uvicorn` quick start.
- **Deploy in a container:** the same README covers Docker, Docker Compose, env vars, and optional Nginx for a private cloud server.

```bash
cd app
cp .env.example .env   # set OPENAI_API_KEY
docker compose up -d
```

API: `POST /brochure` with `{"company_name": "...", "url": "..."}` → returns markdown brochure.

## Requirements

- For notebooks: Python with `openai`, `python-dotenv`, `requests`, `beautifulsoup4` (see root `requirements.txt` or `app/requirements.txt`).
- For the app in Docker: only Docker (and `.env` with `OPENAI_API_KEY`) on the server.
