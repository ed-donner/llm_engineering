# Deal Hunter — PlayStation UK Gift Cards

Multi-agent **Deal Hunter** for PlayStation UK gift card prices, built with **LangGraph**. No local fine-tuned model; **GPT-4o** is used for all reasoning, with a specialist system prompt in the Valuer to simulate pricing expertise.

## Workflow

1. **Searcher Agent** — Finds current UK gift card prices via **Tavily** (CDKeys, ShopTo, Eneba, GAME, etc.).
2. **Valuer Agent** — **GPT-4o** with a specialist system prompt:
   - PlayStation UK cards usually retail at **5–10%** discount.
   - **Strong Buy** = discount **>12%**.
3. **Strategist Agent** — Summarizes findings into a **Gradio** table.

## Setup

From the **repo root** (so `langgraph`, `langchain-openai`, etc. are available):

```bash
# Optional: add Tavily for live search (otherwise placeholder results)
export TAVILY_API_KEY=your_key
export OPENAI_API_KEY=your_key

cd week8/community_contributions/damola-adewunmi
uv run app.py
```

Or install deps in this folder and run:

```bash
pip install -r requirements.txt
python app.py
```

## Project layout

- `state.py` — LangGraph shared state (`DealHunterState`).
- `graph.py` — Builds the graph: **searcher → valuer → strategist**.
- `prompts.py` — **Valuer specialist system prompt** (expertise rules, JSON output).
- `agents/searcher.py` — Tavily search node.
- `agents/valuer.py` — GPT-4o + specialist prompt; parses JSON deals.
- `agents/strategist.py` — Builds table rows for the UI.
- `app.py` — Gradio UI and pipeline entrypoint.

## Valuer prompt (expertise)

The Valuer uses a detailed system prompt in `prompts.py` that:

- Defines **Strong Buy** (>12% discount), **Good/Fair** (5–10%), **Weak/Avoid** (<5% or above face).
- Requires **JSON** output with `retailer`, `denomination_gbp`, `price_gbp`, `discount_pct`, `verdict`, `url`.
- Instructs the model to use **only** information from the provided search results (no hallucination).

This mimics the behaviour of a fine-tuned pricing specialist without training a custom model.
