# Real Estate Comps Agent


A multi-agent system that finds real estate deals by comparing active listings to comparable sold properties (comps) using RAG.

## What It Does

- **Comps** = Comparable sales (recently sold similar properties used to estimate value)
- **Scanner Agent** fetches new property listings (sample data for demo)
- **Comps Agent** uses RAG over a Chroma vector store of sold properties to estimate fair market value
- **Planning Agent** orchestrates the workflow and alerts when a listing is priced below estimate
- **Messaging Agent** sends push notifications via Pushover (optional)

## Prerequisites

- Python 3.11+
- `OPENAI_API_KEY` in `.env`
- Optional: `PUSHOVER_USER` and `PUSHOVER_TOKEN` for push notifications

## Setup

1. **Build the vector store** (run from project root):

   ```bash
   uv run python week8/community_contributions/adams-bolaji/build_vectorstore.py
   ```

2. **Ensure `.env`** has `OPENAI_API_KEY`

## Run

**CLI:**

```bash
uv run python week8/community_contributions/adams-bolaji/run_comps_agent.py
```

**Gradio UI:**

```bash
uv run python week8/community_contributions/adams-bolaji/app.py
```

## File Structure

```
adams-bolaji/
├── agents/
│   ├── comps_agent.py          # RAG-based price estimator
│   ├── listing_scanner_agent.py
│   └── real_estate_planning_agent.py
├── data/
│   ├── sold_properties.json    # Comps data for vector store
│   └── sample_listings.json   # Active listings (demo)
├── models.py
├── build_vectorstore.py
├── real_estate_comps_framework.py
├── run_comps_agent.py
├── app.py
└── README.md
```

## Extending

- Add real listing sources (MLS, Zillow, Redfin APIs or RSS)
- Expand `sold_properties.json` with more comps
- Lower `DEAL_THRESHOLD` in `RealEstatePlanningAgent` for more alerts
