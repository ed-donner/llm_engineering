# Python to TypeScript Code Generator

## What it is

A Python-to-TypeScript code generator that uses a frontier LLM via **OpenRouter** to produce idiomatic, typed TypeScript from Python with equivalent behavior. The interface is a **Gradio app** launched from the notebook.

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

1. Open and run **`week4/IbrahimSheriff/python_to_typescript.ipynb`**.
2. Run all cells to load the client and start the Gradio app.
3. The notebook will print a local URL (e.g. `http://127.0.0.1:7860`). Open it in your browser.
4. Paste or edit Python code, choose a model, click **Convert** to get TypeScript. Use **Run Python** and **Run TypeScript** to compare outputs.

## Optional: Run TypeScript in the app

The **Run TypeScript** button runs the generated code with `npx ts-node`. You need:

- **Node.js** installed.
- **ts-node** available, e.g.:
  - `npm i -g ts-node`, or
  - `npx ts-node main.ts` (uses npx to run ts-node).

If ts-node is not installed, the app will show a message such as:  
`ts-node not found. Install with: npm i -g ts-node (or use npx ts-node)`.
