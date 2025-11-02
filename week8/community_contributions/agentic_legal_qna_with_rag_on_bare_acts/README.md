# Agentic Legal Q&A on Bare Acts (Week 8)

An **agentic RAG** demo that answers legal questions from Indian Bare Acts (IPC/BNS/Constitution).  
Pipeline: **Query expansion (Modal+Qwen3) → Multi-retrieval (Chroma) → Neighbor-aware context merge → LLM answer → Self-critique → Optional second pass**.  
UI: lightweight **Gradio** chat with live agent logs.

## Features
- **Modal-first expander:** `modal_expander.py` (Qwen3-4B via vLLM, GPU) with local LLM fallback.
- **Vector store:** Chroma + `all-MiniLM-L6-v2`, token-span aware chunking, ±neighbor merge.
- **Agentic loop:** critic validates citations and triggers follow-up retrievals if needed.
- **Config knobs:** top-k per rewrite, neighbor radius, max merged blocks, model dropdown.

## Setup
```bash
python -m pip install -U openai chromadb transformers gradio python-dotenv modal
````

Create `.env` with your keys:

```bash
OPENAI_API_KEY=...
```

Place Bare Acts as UTF-8 `.txt` files in:

```
knowledge_base/bare_acts/   # e.g., ipc.txt, bns.txt, coi.txt
```

## Deploy the Modal expander

Set a Modal secret named `huggingface-secret` containing `HUGGINGFACE_HUB_TOKEN`, then:

```bash
modal deploy -m modal_expander
```

## Run the notebook app

```bash
jupyter notebook agentic_legal_qna_with_rag_on_bare_acts.ipynb
```

Run all cells; a Gradio chat appears. Tune **Top-K**, **Neighbor radius**, and **Max blocks** under *Advanced*.

## Notes

* Default OpenAI model: `gpt-4o-mini` (change via UI).
* Vector DB is persisted in `vector_db_w8`; re-run the indexing cell to rebuild after data changes.