# Autonomous Multi-Agent: Africa Flight Prices

An **autonomous multi-agent system** that discovers and ranks **Africa flight prices** by coordinating a Scanner, a Pricer (specialist), a Planner, and a Messaging agent. Built for **week 8** using **week 6** projects as reference (same domain and dataset as [week6/community-contributions/adeyemi-kayode](../../week6/community-contributions/adeyemi-kayode) and [Karosi/africa-flight-prices](https://huggingface.co/datasets/Karosi/africa-flight-prices)).

## Reference

- **Week 6**: Africa flight price fine-tuning (GPT-4o mini), dataset `Karosi/africa-flight-prices`, same schema: `origin_city`, `origin_country`, `destination_city`, `destination_country`, `price_usd`.
- **Week 8**: Multi-agent pattern from `flight_agent_framework.py` and `agents/` (Scanner → Specialist → Planning → Messaging).

## Architecture

| Agent | Role |
|-------|------|
| **Route Scanner** | Produces a list of flight routes to price (from `data/routes.json` or from a natural-language query via optional LLM). |
| **Flight Pricer** | Specialist: looks up price for each route using the Africa flight dataset (Hugging Face or local CSV). |
| **Planning Agent** | Orchestrates: scan → price all routes → rank by price → select best opportunity. |
| **Messaging Agent** | Formats and delivers the best deal (console log + optional Pushover push notification). |

Flow: **Scanner** → **Pricer** → **Planning** (rank) → **Messaging** (alert).

## Contents

- **`agents/`**
  - `agent.py` – Base agent (logging).
  - `flight_deals.py` – Pydantic models: `FlightRoute`, `FlightQuote`, `FlightOpportunity`.
  - `route_scanner_agent.py` – Loads routes from file or parses user query with LLM.
  - `flight_pricer_agent.py` – Looks up price from Karosi/africa-flight-prices (HF or local CSV).
  - `planning_agent.py` – Coordinates scanner, pricer, and messenger.
  - `messaging_agent.py` – Console + optional Pushover alert.
- **`flight_agent_framework.py`** – Main entry: initializes agents, runs one autonomous cycle, persists simple memory.
- **`data/routes.json`** – Sample routes to price (edit to add more).
- **`README.md`** – This file.

## Setup

1. **From repo root** (or this folder):

   ```bash
   pip install datasets pandas requests python-dotenv openai pydantic
   ```

2. **Optional**: Hugging Face token for gated/dataset access:

   ```bash
   export HF_TOKEN=your_token
   ```

   If the Hub dataset is unavailable, place a CSV with columns `origin_city`, `origin_country`, `destination_city`, `destination_country`, `price_usd` at `data/flight_prices_africa.csv` (same format as week6).

3. **Optional (push notifications)**: Set `PUSHOVER_USER` and `PUSHOVER_TOKEN` in `.env` or environment.

4. **Optional (LLM scanner)**: Set `OPENAI_API_KEY` to use natural-language route parsing.

## Run

From this directory:

```bash
# Use routes in data/routes.json (default)
python flight_agent_framework.py

# Parse a natural-language query (requires OPENAI_API_KEY)
python flight_agent_framework.py --query "I want flights from Lagos to Nairobi and Cairo to Johannesburg" --llm-scanner
```

The framework will:

1. Load routes (file or from `--query` if `--llm-scanner`).
2. Look up each route in the Africa flight dataset.
3. Rank by price and pick the best.
4. Log the result and optionally send a push notification.

## Customization

- **More routes**: Edit `data/routes.json` (same structure as in the file).
- **Different data**: Use a CSV at `data/flight_prices_africa.csv` with the same columns as [Karosi/africa-flight-prices](https://huggingface.co/datasets/Karosi/africa-flight-prices).
- **Threshold / filtering**: Extend `FlightPlanningAgent.run_for_routes` (e.g. filter by max price or route count).

This gives you a self-contained **autonomous multi-agent** setup that reuses the **week 6** Africa flight domain and follows the **week 8** agent design (Scanner → Specialist → Planning → Messaging).
