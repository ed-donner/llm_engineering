# 3-Way LLM Communication

A Jupyter notebook that runs a turn-taking debate among three personas — **Alex** (moderator), **Blake**, and **Charlie** — using either paid APIs or a local Ollama model.

## Notebook

- `3_way_communication_LLMs.ipynb` — clients, system prompts, and two debate runs

## What it does

The same three system prompts are used twice:

1. **Paid models** — Alex on OpenAI (`gpt-4.1-mini`), Blake on Anthropic (`claude-sonnet-4-5-20250929`), Charlie on Gemini (`gemini-2.5-pro`). Anthropic and Gemini are called through the OpenAI Python client with compatible `base_url` values.
2. **Ollama as three users** — the same personas, all served by a local Ollama model (default `llama3.2`).

Each speaker sees their own lines as `assistant` and everyone else’s as `user`. Replies are shown as Markdown in the notebook.

## Setup

Python 3.11+ is recommended. From this directory:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root (or this folder, if you run the notebook from here):

```env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
# optional; defaults to http://localhost:11434/v1/
OLLAMA_BASE_URL=http://localhost:11434/v1/
```

## Run

```bash
jupyter notebook 3_way_communication_LLMs.ipynb
```

Run cells from the top. The paid-model debate works without Ollama. For the local three-user run:

```bash
ollama serve
ollama pull llama3.2
```

Use `gpt-oss:20b` only on a machine with at least about 16GB RAM.

## Dependencies

| Package | Use |
| --- | --- |
| `openai` | Chat completions for OpenAI, Anthropic, Gemini, and Ollama |
| `python-dotenv` | Load API keys from `.env` |
| `requests` | Check whether the Ollama server is up |
| `ipython` / `jupyter` / `notebook` | Run the notebook and render Markdown |

## Author

Ravi Soni
