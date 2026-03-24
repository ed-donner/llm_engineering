# Investment Research System (Simplified)

Scanner → RAG Research → LLM Recommendation. Minimal multi-agent pipeline.

## Setup

## Build Vector Store

```bash
python helpers/build_filings_vectorstore.py
```

Uses sample data if `knowledge_base/filings/` is empty. Add `.txt` files named `TICKER_doc_type.txt` for real filings.

## Run

**CLI:** `python research_framework.py`

**UI:** `python price_is_right.py` — click "Run Research" to run a cycle.
