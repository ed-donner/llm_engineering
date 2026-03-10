# Week 8: The Price is Right – Full Pipeline

Full "Price is Right" pipeline using your Week 7 fine-tuned Llama 3.2 3B on Modal and a RAG-based Frontier agent.

## Components

- **Specialist Agent**: Fine-tuned Llama 3.2 3B (QLoRA) on Modal
- **Frontier Agent**: ChromaDB RAG + GPT-4o-mini
- **Ensemble**: 50% specialist + 50% frontier (no neural network)
- **Scanner Agent**: GPT-4o-mini to pick deals from RSS feeds
- **Planning Agent**: Coordinates scan → price → alert
- **Messaging Agent**: Pushover (optional; set `PUSHOVER_USER`, `PUSHOVER_TOKEN`)

## Setup

### 1. Dependencies

```bash
cd week8
uv sync  # or: pip install -r requirements.txt
```

### 2. Environment

Create `.env` in project root:

```
OPENAI_API_KEY=sk-...
HF_TOKEN=hf_...      # for gated models and building vectorstore
MODAL_TOKEN_ID=...   # for Modal (modal token new)
MODAL_TOKEN_SECRET=...
PUSHOVER_USER=...    # optional; enables push notifications on deal click
PUSHOVER_TOKEN=...
```

**Pushover (optional):** If `PUSHOVER_USER` and `PUSHOVER_TOKEN` are set, clicking a deal row in the table triggers a push notification to your device. Sign up at [pushover.net](https://pushover.net).

### 3. Deploy Pricer to Modal

```bash
cd week8
modal deploy community_contributions/winniekariuki/pricer_service.py
```

Update `RUN_NAME` in `pricer_service.py` if your Week 7 run name differs from `2025-03-03-lite`.

### 4. Build ChromaDB Vector Store

```bash
cd week8
uv run python community_contributions/winniekariuki/build_vectorstore.py
```

Creates `products_vectorstore/` in `week8/` from `ed-donner/items_lite`.

### 5. Run the App

```bash
cd week8
uv run python community_contributions/winniekariuki/price_is_right.py
```

Gradio opens in the browser. Deals run every 5 minutes; the table shows deals and estimates. If Pushover is configured, **click a deal row** to send a push notification.
