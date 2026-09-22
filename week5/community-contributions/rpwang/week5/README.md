# rpwang's RAG Application (Week 5)

This app is a standalone RAG assistant that uses the shared knowledge base at `llm_engineering/week5/knowledge-base`

It applies context-window management patterns:
- Structured context budget slots
- Rolling summary for older conversation history
- Token-budget-aware RAG chunk selection
- Evaluator-in-the-loop with retry and context patching
Added more robust handling of LLM's response:
- Handles `reasoning_content` from some LLMs's response
Support switch between OPEN ROUTER, OPEN AI, and local LLM(Ollama)

## Files

- `app.py` — Gradio chat UI
- `rag.py` — retrieval + response logic with context budgeting
- `ingest.py` — indexes markdown documents from `week5/knowledge-base`
- `vector_db/` — local Chroma persistence (created automatically)
- `eval.py` - modified from llm_engineering\week5\evaluation\eval.py to fit rag.py
- `evaluator.py` - Execute eval.py using the same test cases in week 5 execrise

## Use with local Ollama (recommended for your setup)

You can run this app with your local model `gemma4:e2b`.

On first run, if no local vector database exists, ingestion runs automatically.
