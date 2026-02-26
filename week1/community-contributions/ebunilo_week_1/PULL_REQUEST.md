# Pull Request: ebunilo_week_1 – Week 1 notebooks, exercise & containerized brochure app

## Summary

This PR adds Week 1 community contributions: **Day 1 with Ollama**, the **Week 1 Exercise (technical tutor)** using OpenAI and Ollama, shared **scraper** and **env** setup, and a **containerized Company Brochure Generator** (Day 5 business solution) with Docker/Docker Compose and READMEs for deployment on a private cloud server.

## What’s included

### Notebooks & shared code

- **`day1_with_ollama.ipynb`** – Day 1 notebook using Ollama (local LLM).
- **`week1 EXERCISE.ipynb`** – Technical tutor: answers technical questions about Python, software engineering, data science, and LLMs using **OpenAI (gpt-4o-mini)** and **Ollama (Llama 3.2)** with streaming Markdown responses.
- **`scraper.py`** – Shared website scraper (fetch links and page content).
- **`requirements.txt`** / **`env.example`** – Dependencies and env template for notebooks.

### Company Brochure Generator (Day 5 app)

- **`app/`** – Web API and containerization for the Day 5 “full business solution”:
  - **`main.py`** – FastAPI app: `GET /health`, `POST /brochure` (company name + URL → markdown brochure).
  - **`brochure.py`** – Brochure logic: LLM-based link selection and brochure generation (aligned with day5 notebook).
  - **`scraper.py`** – App-local scraper (timeouts, error handling).
  - **`requirements.txt`** – FastAPI, uvicorn, openai, requests, beautifulsoup4, etc.
  - **`Dockerfile`** – Python 3.12-slim, non-root user, port 8000.
  - **`docker-compose.yml`** – Single service, env_file, healthcheck.
  - **`.env.example`** – `OPENAI_API_KEY` and optional model/port.
  - **`.dockerignore`** – Lean build context.
  - **`app/README.md`** – Local run, Docker, Docker Compose, Nginx, API usage.

### Documentation

- **`README.md`** (repo root for this contribution) – Overview of the folder, table of contents, link to app deployment and requirements.

## Why it’s useful

- **Exercise**: Dual backends (OpenAI + Ollama), streaming Markdown, reusable technical tutor aligned with Week 1.
- **Brochure app**: Day 5 pipeline as a deployable service; one-command run with Docker Compose and clear steps for a private cloud server.
- **Single PR**: One place for notebooks, shared code, and production-style deployment of the Week 1 Day 5 solution.

## How to run

### Notebooks

1. Copy `env.example` to `.env`, set `OPENAI_API_KEY`. For Ollama: `ollama serve` and `ollama pull llama3.2`.
2. Open `day1_with_ollama.ipynb` or `week1 EXERCISE.ipynb` and run cells.

### Brochure app (local)

```bash
cd app
cp .env.example .env   # set OPENAI_API_KEY
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Brochure app (Docker / private cloud)

```bash
cd app
cp .env.example .env   # set OPENAI_API_KEY
docker compose up -d
```

See **`app/README.md`** for full deployment options (plain Docker, Nginx, env vars).

## Checklist

- [x] Week 1 Exercise: technical tutor with OpenAI and Ollama, streaming Markdown.
- [x] Day 1 with Ollama notebook.
- [x] Shared scraper and env example.
- [x] Day 5 brochure pipeline as FastAPI app.
- [x] Dockerfile and docker-compose for container deployment.
- [x] README at contribution root and app-level deployment README.

## Author

ebunilo – Week 1 community contribution (LLM Engineering course).
