# Research Assistant with Tool Calling (Agentic Workflow)

A research assistant that uses **OpenAI-style tool calling**: one LLM decides which tools to call and in what order. You interact via a **Gradio Chat Interface** with full conversation history in context.

## What it does

- **Tools:** `search_topics` (over a small knowledge base in `knowledge_base.py`), `summarize_text`, `get_citation`, `format_report`
- **Flow:** You ask a question in the chat → the model calls tools in sequence → the loop runs until done → the model replies with a short report (and citations when relevant)
- **Multi-turn:** Chat history is passed into the assistant so follow-up questions (e.g. “expand on that”, “same topic with citations”) use prior context

## Setup

- Put `OPENAI_API_KEY` in `.env` (or export it). For **OpenRouter** keys (`sk-or-...`), the notebook uses `https://openrouter.ai/api/v1` by default.
- Install dependencies, e.g. `pip install openai python-dotenv gradio`
- Ensure `knowledge_base.py` is in the same folder (or on the path the notebook adds) so the tools can load it.

## Run

1. Open `research_assistant_agent.ipynb` and run all cells in order (imports, tools, agent loop, then Gradio).
2. The last cell launches a **Gradio Chat Interface**. Use the in-notebook app or the URL (e.g. `http://127.0.0.1:7860`) to chat with the research assistant.
3. Try the example prompts or type your own; the assistant will search, summarize, cite, and format reports.

## Files

- **research_assistant_agent.ipynb** — Setup, knowledge-base import, tool implementations, tool definitions, agent loop (`run_research_assistant` with optional history), and Gradio Chat Interface.
- **knowledge_base.py** — Stub knowledge base (topic → id, text, author, year) used by `search_topics` and `get_citation`.
- **README.md** — This file.
