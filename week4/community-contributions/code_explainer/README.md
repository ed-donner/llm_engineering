# Code → One-Page Explanation

**Week 4 community contribution** — Turn a single file or a few related functions into:

- A short **summary** of what the code does  
- **Control flow** and **data flow** bullet points  

No code conversion; explanation only. Uses **OpenRouter** by default.

## How to run

1. From the repo root, ensure dependencies are installed: `uv sync` (or `pip install -e .`).
2. Set `OPENROUTER_API_KEY` in a `.env` file (e.g. in repo root or this folder).
3. Open `code_to_explanation.ipynb` and run all cells. The last cell launches a Gradio UI.
4. Paste your code in the text box, choose a model (default: `openai/gpt-4o-mini`), and click **Explain**.

## Output

Markdown with **Summary**, **Control flow**, and **Data flow** sections.

## Requirements

- Python 3.11+
- `openai`, `python-dotenv`, `gradio` (from repo `pyproject.toml`)
