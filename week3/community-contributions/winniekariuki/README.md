# Week 3 Exercise – Synthetic Data Generator (winniekariuki)

**Synthetic Data Generator** is the Week 3 community contribution: a tool that generates structured synthetic datasets from a natural-language description. Uses **OpenAI** (GPT-4o-mini) and **Llama** (Ollama) with multiple prompt templates for diverse outputs, and a **Gradio UI**.

## What's included

- **Models**: OpenAI (gpt-4o-mini) and Llama 3.2 via Ollama — same setup as Week 2.
- **Diverse prompts**: Preset templates (customer reviews, product catalog, support tickets, job postings, survey responses) plus custom scenario for varied synthetic data.
- **Output formats**: JSON array or CSV; configurable number of rows.
- **Gradio UI**: Scenario description, row count, format, prompt style, and model selector; raw output for copy.

## How to run

1. From repo root (or from `week3/community-contributions/winniekariuki/`), ensure dependencies are installed: `openai`, `gradio`, `python-dotenv`.
2. Set `OPENAI_API_KEY` in `.env` for GPT.
3. For Llama: have **Ollama** running locally with `llama3.2` (e.g. `ollama run llama3.2`).
4. Open `week3_exercise.ipynb` and run all cells. The Gradio app will launch in your browser.

## Dependencies

Uses the course stack: `openai`, `gradio`, `python-dotenv`. No Hugging Face or Colab-specific code; runs locally.
