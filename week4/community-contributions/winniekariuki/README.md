# Week 4 Exercise – Code Generator (winniekariuki)

**Code Generator** is the Week 4 community contribution: a tool that uses LLMs to convert Python to C++, add docstrings and comments, and generate unit tests. Uses **OpenAI** (GPT-4o-mini) and **Llama 3.2** (Ollama), with a **Gradio UI**.

## What's included

- **Models**: OpenAI (gpt-4o-mini) and Llama 3.2 via Ollama — same setup as Week 2 & 3.
- **Actions**: Convert Python to C++, add docstrings/comments, write pytest unit tests.
- **Gradio UI**: Dropdown to select action; paste Python code, pick action and model, generate output.
- **Output**: Raw code only (strips markdown code blocks when present).

## How to run

1. From repo root (or from `week4/community-contributions/winniekariuki/`), ensure dependencies are installed: `openai`, `gradio`, `python-dotenv`.
2. Set `OPENAI_API_KEY` in `.env` for GPT.
3. For Llama: have **Ollama** running locally with `llama3.2` (e.g. `ollama run llama3.2`).
4. Open `week4 EXERCISE.ipynb` and run all cells. The Gradio app will launch in your browser.

## Dependencies

Uses the course stack: `openai`, `gradio`, `python-dotenv`. No Hugging Face or Colab-specific code; runs locally.
