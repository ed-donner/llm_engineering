## Week 1 — Ollama Web Summarizer

This folder contains a clean, minimal solution that mirrors `week1/day1.ipynb`, but uses Ollama (OpenAI-compatible endpoint) instead of GPT. It scrapes a webpage and summarizes it locally using an Ollama model.

### Files
- `w1d1-ollama-web-summarizer.ipynb`: Single-URL webpage summarizer using Ollama
- `utils.py`: Simple HTML scraper helpers (BeautifulSoup)
- `requirements.txt`: Minimal deps for the notebooks
- `env.example`: Example env values (copy to `.env` if needed)

### Quickstart
```bash
cd community-contributions/haben/week1
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.2    # or llama3.2:1b on smaller machines
cp env.example .env     # optional
```

Open the notebook `w1d1-ollama-web-summarizer.ipynb` and run cells. By default:
- `OLLAMA_BASE_URL=http://localhost:11434/v1`
- `OLLAMA_MODEL=llama3.2`
- `WEBSITE_URL=https://edwarddonner.com`
- `LOG_LEVEL=INFO`

### Usage tips
- Change the target site by setting `WEBSITE_URL` in `.env` (or export before running).
- If your machine is resource-constrained, set `OLLAMA_MODEL=llama3.2:1b`.
- Increase verbosity by setting `LOG_LEVEL=DEBUG`.

### Troubleshooting
- Ensure the Ollama server is running: visit `http://localhost:11434/` (should say “Ollama is running”). If not, run `ollama serve`.
- If requests fail or are slow, try another site or reduce the character limit in code.
- For SSL/network issues, confirm you can `curl` the site and that firewalls/proxies allow outbound HTTP(S).

### Notes
- The notebook preserves the Day 1 structure (prompts → messages → summarize → display) while swapping GPT for Ollama’s OpenAI-compatible `/v1/chat/completions`.
- Logging and basic error handling are included around scraping and LLM calls for robustness.