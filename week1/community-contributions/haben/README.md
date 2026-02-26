## Week 1 — Community Contributions

This folder contains clean, minimal solutions for Week 1 exercises.

### Files
- `w1d1-ollama-web-summarizer.ipynb`: Single-URL webpage summarizer using Ollama (mirrors `week1/day1.ipynb`)
- `w1d5-brochure-builder.ipynb`: Company brochure builder (implements `week1/day5.ipynb` business challenge)
- `utils.py`: Simple HTML scraper helpers (BeautifulSoup)
- `requirements.txt`: Minimal deps for the notebooks
- `env.example`: Example env values (copy to `.env` if needed)

### Quickstart
```bash
cd week1/community-contributions/haben
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.2    # or llama3.2:1b on smaller machines
cp env.example .env     # optional
```

### w1d1-ollama-web-summarizer.ipynb

Single-URL webpage summarizer using Ollama (OpenAI-compatible endpoint) instead of GPT.

**Quickstart:**
```bash
ollama pull llama3.2    # or llama3.2:1b on smaller machines
```

Open the notebook and run cells. By default:
- `OLLAMA_BASE_URL=http://localhost:11434/v1`
- `OLLAMA_MODEL=llama3.2`
- `WEBSITE_URL=https://edwarddonner.com`
- `LOG_LEVEL=INFO`

**Usage tips:**
- Change the target site by setting `WEBSITE_URL` in `.env` (or export before running).
- If your machine is resource-constrained, set `OLLAMA_MODEL=llama3.2:1b`.
- Increase verbosity by setting `LOG_LEVEL=DEBUG`.

**Troubleshooting:**
- Ensure the Ollama server is running: visit `http://localhost:11434/` (should say "Ollama is running"). If not, run `ollama serve`.
- If requests fail or are slow, try another site or reduce the character limit in code.
- For SSL/network issues, confirm you can `curl` the site and that firewalls/proxies allow outbound HTTP(S).

### w1d5-brochure-builder.ipynb

Company brochure builder that creates professional brochures from website content.

**Quickstart:**
```bash
# Ensure you have OPENROUTER_API_KEY in your .env file
cp env.example .env
# Edit .env and add: OPENROUTER_API_KEY=sk-or-...
```

**Usage:**
```python
# Standard generation
create_brochure("Company Name", "https://company-website.com")

# Streaming version
create_brochure("Company Name", "https://company-website.com", stream=True)
```

**Configuration:**
- `OPENROUTER_API_KEY`: Your OpenRouter API key (required)
- `OPENROUTER_MODEL`: Model to use (default: `openai/gpt-4o-mini`)

### Notes
- Both notebooks include error handling for robustness.
- The Day 1 notebook uses Ollama for local inference.
- The Day 5 notebook uses OpenRouter and demonstrates Agentic AI patterns with sequential LLM calls.