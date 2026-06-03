# AI Deal Finder

An agent-orchestrated deal finder for **Jumia Kenya**. Type a product query, and the pipeline scrapes live listings, estimates fair market prices using a fine-tuned Llama model, and tells you whether each product is a good deal.

---

## How It Works

```
User query
    │
    ▼
PlanningAgent          ← orchestrator
    ├── ScraperAgent   ← GPT-4o-mini + tool calling → 5 structured products
    └── PricingAgent   ← fine-tuned Llama on Modal GPU → price estimate + verdict
```

**PlanningAgent** coordinates the pipeline end-to-end. It calls `ScraperAgent` to discover products, then hands them to `PricingAgent` for valuation, and returns the final enriched list to the Gradio UI.

**ScraperAgent** uses GPT-4o-mini (via OpenRouter) in a tool-calling loop. The model decides which Jumia URL to fetch, calls the `scrape_url` tool, reads the cleaned page text, and extracts exactly 5 structured products.

**PricingAgent** calls a PEFT/LoRA fine-tuned Llama-3.2-3B model deployed on a Modal T4 GPU. For each product it returns an estimated fair USD price and a deal verdict based on percentage savings.

### Verdict formula

```
savings_pct = (estimated_price − scraped_price) / estimated_price × 100
```

| Verdict | Condition |
|---|---|
| 🔥 Great Deal | ≥ 20% below estimate |
| ✅ Good Deal | ≥ 5% below estimate |
| 🟡 Fair Price | within ±5% of estimate |
| ❌ Overpriced | > 5% above estimate |

---

## Project Structure

```
week8-project/                # Gradio UI entry point
├── app.ipynb                 # Notebook version of the UI
├── pricer_service.py         # Modal cloud GPU service (deploy once)
├── tools.py                  # HTTP scraper utility
├── requirements.txt
└── agents/
    ├── __init__.py
    ├── planning_agent.py     # Orchestrator
    ├── scraper_agent.py      # Jumia scraper agent
    └── pricing_agent.py      # Price estimation agent
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set environment variables

Create a `.env` file in `week8-project/`:

```env
OPENROUTER_API_KEY=your_openrouter_key
```

Add your HuggingFace token as a Modal secret (used by the pricer service):

```bash
modal secret create huggingface-secret HF_TOKEN=your_hf_token
```

### 3. Deploy the pricing model to Modal

```bash
cd week8-project
modal deploy pricer_service.py
```

This deploys your fine-tuned Llama model to Modal's cloud and keeps it warm for fast inference. Only needs to be done once (or after changes to `pricer_service.py`).

### 4. Run the app

```bash
python app.py
```

Or run the `app.ipynb` notebook cell directly.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration LLM | GPT-4o-mini via [OpenRouter](https://openrouter.ai) |
| Pricing model | Fine-tuned Llama-3.2-3B (PEFT/LoRA) |
| Cloud GPU inference | [Modal](https://modal.com) — NVIDIA T4 |
| Model quantization | `bitsandbytes` 4-bit NF4 |
| Web scraping | `httpx` + `BeautifulSoup4` + `lxml` |
| Bot evasion | `fake-useragent` |
| UI | [Gradio](https://gradio.app) |
| Data source | [Jumia Kenya](https://www.jumia.co.ke) |
