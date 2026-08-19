# WCAG Accessibility Auditor - Day 1

Baseline RAG implementation using keyword retrieval on WCAG 2.2 success criteria.
Demonstrates how keyword search fails on natural language before introducing embeddings in later days.

## Files

| File | Purpose |
|---|---|
| `wcag_day1_practice.ipynb` | Main notebook — keyword retriever + Gradio chat |
| `build_knowledge_base.py` | Fetches WCAG 2.2 from W3C and generates the knowledge base |
| `NOTICE.md` | W3C attribution for the derived WCAG content |

## Setup

**1. Install dependencies**
```bash
pip install httpx openai python-dotenv gradio
```

**2. Build the knowledge base**
```bash
python build_knowledge_base.py
```
Downloads WCAG 2.2 from the public W3C source and writes 86 Markdown files to
`knowledge-base/a11y/success-criteria/`. No API key needed, takes a few seconds.

**3. Add your OpenAI key to `.env`**
```
OPENAI_API_KEY=sk-...
```

**4. Run the notebook**

Open `day1_exr.ipynb` and run all cells.

## What it shows

Keyword retrieval only works when the user types the exact vocabulary the documents use.
"pointer" succeeds, "touch" refused even though the relevant criteria (2.5.1, 2.5.2)
are in the knowledge base. A strict grounding prompt surfaces these failures as honest
refusals rather than letting the model answer from memory.

See `NOTICE.md` for licensing information.