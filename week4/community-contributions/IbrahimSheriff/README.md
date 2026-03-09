# Week 4: Code gen and unit-test AI

## What it is

A **Gradio app** (launched from the notebook) that uses a frontier LLM via **OpenRouter** to:

- **Convert Python → TypeScript** — Generate idiomatic, typed TypeScript from Python with equivalent behavior.
- **Run code** — Run the Python or TypeScript in the app and compare outputs.
- **Generate unit tests** — Choose **Python** (pytest) or **TypeScript** (Jest) and generate tests for the code in the corresponding box.

Notebook: **`week4/python_to_typescript.ipynb`**.

## Setup

1. **API key:** Put your OpenRouter API key in a `.env` file in the repo root:

   ```
   OPENROUTER_API_KEY=sk-or-v1-...
   ```

   Get a key at [openrouter.ai](https://openrouter.ai).

2. **Dependencies:** From the repo root run:
   ```bash
   uv sync
   ```
   Or install: `python-dotenv`, `openai`, `gradio`.

## How to run

1. Open and run **`week4/python_to_typescript.ipynb`**.
2. Run all cells to load the client and start the Gradio app.
3. Use the local URL (e.g. `http://127.0.0.1:7860`) in your browser.
4. **Convert:** Paste Python, pick a model, click **Convert** to get TypeScript.
5. **Run:** Use **Run Python** and **Run TypeScript** to see outputs.
6. **Unit tests:** Choose **Python** or **TypeScript** in the dropdown and click **Generate unit tests** to get pytest or Jest tests.

## Optional: Run TypeScript in the app

The **Run TypeScript** button uses `npx tsx` (or `npx ts-node`). You need:

- **Node.js** installed.
- **tsx** or **ts-node**, e.g.:
  - `npx tsx` (recommended, no global install),
  - or `npm i -g ts-node`.

If neither is available, the app will show an install message.
