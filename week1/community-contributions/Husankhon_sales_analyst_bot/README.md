# 📊 Sales Data Analyst Bot

**Week 1 Community Contribution — LLM Engineering Course (Ed Donner)**

A natural-language analytics assistant that reads a CSV file of sales data and answers business questions using frontier LLMs.

## What it does

- Loads any sales CSV and injects it into the LLM prompt (context stuffing)
- Supports **OpenAI GPT**, and **Ollama** (local, free)

## Files

| File | Description |
|------|-------------|
| `sales_analyst_bot.ipynb` | Main notebook — run top to bottom |
| `sales_data.csv` | Sample 50-row sales dataset |
| `README.md` | This file |

## How to use

1. Add your API keys to `.env` in the project root:
   ```
   OPENAI_API_KEY=sk-...
   ```

2. Open `sales_analyst_bot.ipynb` in Cursor/Jupyter and run all cells.

3. Swap in your own CSV — just change `CSV_PATH` in Cell 2.

## Example questions to try

- *"Which product generated the highest revenue?"*
- *"Who is the top salesperson by profit margin?"*
- *"Compare Q1 vs Q2 — is the business growing?"*
- *"Which region is underperforming and why?"*

## Skills practised (Week 1)

- OpenAI Chat Completions API
- Ollama (local models, OpenAI-compatible)
- System prompt engineering
