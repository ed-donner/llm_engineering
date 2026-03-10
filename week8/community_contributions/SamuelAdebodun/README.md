# Week 8 — Stack Health Monitor (SamuelAdebodun)

Scans a repo for **requirements.txt**, **package.json**, and **Dockerfile** (FROM lines). Enriches deps with latest-version info (mock data), adds a bit of RAG context (upgrade notes), and uses an LLM to report **Upgrade** / **Replace** / **Watch**. Optional **memory.json** tracks what changed since last run.

Same model choices as other weeks: OpenAI, Anthropic, or Ollama. One notebook, Gradio at the end.

**How to run:** Open `week8.ipynb`, set `.env` (e.g. `OPENAI_API_KEY`), run all cells. In the UI, enter a path to the repo (e.g. `/path/to/llm_engineering` or `.` for current dir) and click Run report. If you see "No dependencies", use the full path to the folder that *contains* `requirements.txt` (or package.json / Dockerfile).
