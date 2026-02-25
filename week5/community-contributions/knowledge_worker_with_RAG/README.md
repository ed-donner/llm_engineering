# LiteLLM RAG Knowledge Worker

RAG chatbot over LiteLLM documentation. Uses OpenAI `text-embedding-3-small` and `gpt-4o-mini`; Chroma for vector store; Gradio UI.

**Setup:** From repo root, ensure `.env` has `OPENAI_API_KEY`. In this directory run `uv sync`.

**Steps:**
1. **Build knowledge base:** `uv run scripts/build_knowledge_base.py` (clones LiteLLM repo, copies docs into `knowledge-base/`).
2. **Ingest:** `uv run ingest.py` (chunks docs, embeds, writes to `vector_db/`).
3. **Run app:** `uv run app.py` (Gradio chat at http://localhost:7860).

## Evaluation

Evaluation files are in `evaluation/`:
- `evaluation/tests.jsonl` - test set (question, keywords, reference answer, category)
- `evaluation/test.py` - test loader/model
- `evaluation/eval.py` - retrieval + answer evaluation CLI

Run a single test by row number:
- `uv run evaluation/eval.py 0`

Run all tests with aggregate metrics:
- `uv run evaluation/eval.py --all`

Metrics:
- Retrieval: `MRR`, `nDCG`, `keyword_coverage`
- Answer quality (LLM-as-a-judge): `accuracy`, `completeness`, `relevance` (1-5)

