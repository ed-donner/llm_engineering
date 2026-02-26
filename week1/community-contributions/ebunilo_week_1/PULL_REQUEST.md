# Pull Request: Week 1 Exercise – Technical Tutor (OpenAI + Ollama)

## Summary

This PR adds a **technical tutor** notebook for the Week 1 end-of-week exercise. The tool answers technical questions about Python code, software engineering, data science, and LLMs using both **OpenAI (gpt-4o-mini)** and **Ollama (Llama 3.2)**, with streaming responses rendered as Markdown.

## What’s included

- **`week1 EXERCISE.ipynb`** – Main notebook implementing the technical tutor:
  - System prompt: *"You are a helpful technical tutor who answers questions about python code, software engineering, data science and LLMs."*
  - **OpenAI**: `gpt-4o-mini` via the OpenAI API (uses `OPENAI_API_KEY` from env).
  - **Ollama**: `llama3.2` via the OpenAI-compatible API at `http://localhost:11434/v1`.
  - Streaming completions from both models with Markdown display.
  - Example question (editable in-cell) demonstrating a Python snippet explanation (e.g. `yield from` with a set comprehension).

- **Dependencies**: Uses `openai`, `python-dotenv`, and `IPython` (and optionally `scraper` from the same folder if you use other notebooks here; the exercise itself only needs the clients and display).

## Why it’s useful

- **Dual backends**: Compare cloud (OpenAI) vs local (Ollama) in one notebook.
- **Reusable**: Change the `question` variable and re-run to get tutor answers on new topics.
- **Streaming + Markdown**: Responses stream and render as formatted Markdown for readability.
- **Aligned with course**: Demonstrates OpenAI API and Ollama usage as in Week 1.

## How to run

1. **Environment**
   - Create a `.env` with `OPENAI_API_KEY` for the OpenAI part.
   - For Ollama: run `ollama serve` and `ollama pull llama3.2` (or equivalent).

2. **Notebook**
   - Open `week1 EXERCISE.ipynb` and run cells in order.
   - Edit the `question` string in the notebook to ask new technical questions.
   - Run the GPT and/or Llama cells to get streaming tutor answers.

## Checklist

- [x] Implements a tool that takes a technical question and responds with an explanation.
- [x] Uses the OpenAI API (gpt-4o-mini).
- [x] Uses Ollama (Llama 3.2) via the OpenAI-compatible API.
- [x] Suitable for use as a personal technical tutor during the course.

## Author

ebunilo – Week 1 community contribution (LLM Engineering course).
