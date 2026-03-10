# AI Dataset Generator (Week 3)

Generate **mock/dummy tabular data** from a short description (e.g. airline bookings, insurance claims, e-commerce orders). The app uses an LLM to produce structured JSON, then shows a table and lets you **export as CSV or JSON**.

## Concepts used (Weeks 1–3)

- **Week 1 (Day 2):** Uses the **OpenAI Python client** for most providers. We have a free Gemini API Key to save on costs. Same `OpenAI()` client with different `base_url` and `api_key` for OpenAI, Gemini, OpenRouter, and Ollama (OpenAI-compatible endpoints).
- **Week 2:** Single backend (`dataset_generator.py`) and a thin UI (Gradio in `notebook.ipynb`).
- **Week 3:** Dynamic, user-driven data description (any domain: airline, insurance, etc.) and structured output (columns + rows) for export.

## Providers

| Provider       | Env var              | Example models                                     |
| -------------- | -------------------- | -------------------------------------------------- |
| **OpenAI**     | `OPENAI_API_KEY`     | gpt-4o-mini, gpt-4o                                |
| **OpenRouter** | `OPENROUTER_API_KEY` | openai/gpt-4o-mini, anthropic/claude-3-haiku       |
| **Gemini**     | `GOOGLE_API_KEY`     | gemini-2.0-flash, gemini-1.5-flash, gemini-1.5-pro |
| **Ollama**     | (none)               | llama3.2:1b, deepseek-r1:1.5b                      |

- **Ollama:** run `ollama serve` and pull a model (e.g. `ollama pull llama3.2:1b`).
- **Gemini:** get a free API key at [Google AI Studio](https://aistudio.google.com/api-keys) and set `GOOGLE_API_KEY` in `.env`. Uses the same OpenAI-compatible client with Google’s base URL.

## Setup

1. Clone and go to this folder:
   ```bash
   cd week3/community-contributions/makinda
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and set at least one key (or use Ollama with no key):
   - `OPENAI_API_KEY` for OpenAI
   - `OPENROUTER_API_KEY` for OpenRouter
   - `GOOGLE_API_KEY` for Gemini

## Run

From this folder, open and run `notebook.ipynb` (e.g. in Jupyter or VS Code). Run all cells; the last cell launches the Gradio app. In the UI:

1. **Describe dataset** — e.g. “20 rows of airline bookings with flight number, origin, destination, date”.
2. **Provider** — OpenAI, OpenRouter, Gemini, or Ollama.
3. **Model** — list updates when you change provider.
4. **Export format** — CSV or JSON.
5. Click **Generate**, then use **Download File** to save.

## Project structure

```
makinda/
├── dataset_generator.py   # Backend: OpenAI client, multi-provider, generate + export
├── notebook.ipynb         # Gradio UI
├── requirements.txt
├── .env.example
└── README.md
```
