# Day 1: Website Summarizer with Local Ollama

[`day1.ipynb`](day1.ipynb) recreates the Week 1 website-summarization lab using a locally hosted Ollama model. It fetches webpage text, builds system and user messages, asks the model for a concise Markdown summary, and displays the result. It uses Ollama's OpenAI-compatible chat endpoint; a cloud API key is not required.

## Requirements

- Python notebook kernel with `python-dotenv`, `requests`, `beautifulsoup4`, and `openai`. The first notebook cell installs these packages.
- Ollama installed and running locally.
- A model pulled into Ollama and named in the `.env` configuration.
- Internet access for the example webpages. The notebook scrapes the configured sample site and CNN, so running all cells makes external web requests as well as local model calls.

## Configure Ollama

Create a `.env` file in this directory, beside `day1.ipynb`. **There is no `.env` file in this directory by default.** Do not commit a local `.env` file if it contains private values.

```dotenv
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=your-installed-model

# Optional settings; these are the notebook defaults.
OLLAMA_TIMEOUT_SECONDS=120
OLLAMA_TEMPERATURE=0
OLLAMA_MAX_TOKENS=1024
OLLAMA_TOP_P=1
OLLAMA_SEED=42
OLLAMA_MAX_RETRIES=2
OLLAMA_API_KEY=ollama
```

Replace `your-installed-model` with a model available in your Ollama installation. For example, pull one from a terminal with `ollama pull <model-name>`. Start Ollama with `ollama serve` if it is not already running. The notebook adds `/v1` to the base URL when needed and checks the server's installed models without printing `.env` values.

## Run the Notebook

1. Open `day1.ipynb` and select a Python kernel.
2. Run the first cell to install dependencies. Restart the kernel if prompted, then continue from the top.
3. Run the `.env` configuration and client cells. The notebook expects its working directory to be this folder so it can find `.env`.
4. Run the remaining cells in order. They test a single prompt, check Ollama connectivity and model availability, summarize the sample website, and then summarize CNN in the final example cell.

If Ollama is unavailable or the model is missing, the diagnostic section reports the issue and suggests the next step. For website fetch errors, check the URL and your network access; some JavaScript-heavy or access-protected sites cannot be handled by the simple HTML scraper.

## Notebook Contents

- A self-contained website scraper with request timeouts, HTML cleanup, and a 2,000-character text limit.
- Prompt formatting and reusable `summarize(url)` / `display_summary(url)` helpers.
- Optional two-stage summarization, streamed output, and JSON response parsing.
- Bounded retries for transient Ollama failures and configurable timeout/model parameters.
- Prompt and JSON parsing assertions near the end of the notebook.
- A saved JSON artifact at `artifacts/day1_summary.json` when the sample summary is available. The artifact includes the URL, model name, generation parameters, and summary, but not `.env` values.
