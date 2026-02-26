# Pull Request: Week 1 Exercise (Frank Asket)

## Title (for GitHub PR)

**Week 1 Exercise: Technical Q&A tool + bilingual website summarizer (asket)**

---

## Description

This PR adds my **Week 1 Exercise** notebook to `community-contributions/asket/week1/`. It demonstrates use of the OpenAI API (via OpenRouter), streaming, and Ollama.

### Author

**Frank Asket** ([@frank-asket](https://github.com/frank-asket)) – Founder & CTO building Human-Centered AI infrastructure.

---

## What's in this submission

| Item | Description |
|------|-------------|
| **week1_EXERCISE.ipynb** | Single notebook with two parts. |

### Part 1: Technical Q&A tool

- **Goal:** A reusable tool for the course: ask a technical question and get an explanation.
- **Stack:** GPT (streaming) via **OpenRouter** (`OPENROUTER_API_KEY`); optional **Ollama** (Llama 3.2) for a second answer.
- **Flow:** Set a `question` (e.g. "Explain this code: …"), build system + user prompts, call the API with streaming, show markdown. Includes `strip_code_fence()` so model output isn't wrapped in extra code blocks.
- **Optional cell:** Uses Ollama to get a second answer (no API key); tries `llama3.2:1b` then `llama3.2:3b` with a short fallback message if Ollama isn't available.

### Part 2: Bilingual website summarizer (Ollama only)

- **Goal:** Summarize a webpage in **English** and in **Guéré** (Ivorian language), separated by `<hr>`.
- **Stack:** **Ollama only** (no API key). Uses `week1/scraper` (`fetch_website_contents`); path is set so the notebook runs from repo root or from `community-contributions/asket/`.
- **How to run:** From repo root, ensure Ollama is running (`ollama serve`) and pull a model (`ollama pull llama3.2`). Set the URL in the notebook (default example: https://github.com/frank-asket).

---

## Technical notes

- **API:** Part 1 uses **OpenRouter** (`OPENROUTER_API_KEY`, `base_url="https://openrouter.ai/api/v1"`). Falls back to `OPENAI_API_KEY` or default `OpenAI()` if OpenRouter is not set.
- **Scraper:** Notebook adds `week1` to `sys.path` so `from scraper import fetch_website_contents` works when run from repo root or from the asket folder.
- **Models:** Part 1 uses `gpt-4o-mini` (OpenRouter) and optionally `llama3.2:3b-instruct-q4_0` / `llama3.2:1b-instruct-q4_0` (Ollama). Part 2 uses Ollama only.

---

## Checklist

- [x] Changes are under `community-contributions/asket/week1/`.
- [ ] **Notebook outputs:** Clear outputs before merge if required by the repo.
- [x] No edits to owner/main repo files outside this folder.
- [x] Uses existing `week1/scraper`; no new dependencies beyond course setup.

---

## How to run

1. **Part 1 (Q&A):** Set `OPENROUTER_API_KEY` (or `OPENAI_API_KEY`) in `.env`. Run cells from the top; change `question` and re-run the streaming cell. Optionally run the Ollama cell (requires `ollama serve` and `ollama pull llama3.2`).
2. **Part 2 (Summarizer):** Run from repo root. Start Ollama (`ollama serve`, `ollama pull llama3.2`). Set the URL in the notebook and run the summarizer cells.

Thanks for reviewing.
