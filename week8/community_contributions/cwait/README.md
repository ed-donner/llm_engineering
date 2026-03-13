# Quote / Tip of the Day Agent — cwait (Week 8)

A simple agent that fetches quotes from a public API, uses an LLM to pick one and rephrase it as a "tip of the day", and displays it in a Gradio UI.

## What it does

1. **Fetch** — Gets quotes from [quotable.io](https://quotable.io) (no API key).
2. **Pick** — An LLM chooses the most inspiring quote and rewrites it as a short tip (1–2 sentences).
3. **Display** — Gradio app with a **Refresh** button to get a new tip.

## How to run

1. Ensure `OPENAI_API_KEY` is set (e.g. in a `.env` in the project root).
2. Open `cwait-igniters-week8.ipynb` and run all cells, or run from the **week8** directory so `agents` can be imported:
   ```bash
   cd week8
   jupyter notebook community_contributions/cwait/cwait-igniters-week8.ipynb
   ```
3. Run the Gradio cell to launch the UI; click **Refresh** for a new tip.

## Requirements

- Python with `requests`, `openai`, `gradio`, `python-dotenv`
- Course `week8` agents on path (notebook sets this up when run from `community_contributions/cwait`)
