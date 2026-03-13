# README (`_ollama_HF` Pipeline)

## What This Version Is
This is the local RAG pipeline based on:

- `Ollama` for local LLM inference
- `HuggingFace` embeddings
- `Chroma` as vector database
- `Gradio` for chat and evaluation UI

This is the main version to keep in `week5`.

## What Each `_ollama_HF` File Does

### `pro_implementation/ingest_ollama_HF.py`
- Loads markdown documents from `knowledge-base/`
- Uses a local Ollama model to split documents into structured chunks
- Creates HuggingFace embeddings for those chunks
- Writes vectors and metadata into Chroma at `preprocessed_db/`

### `pro_implementation/answer_ollama_HF.py`
- Opens the Chroma collection
- Embeds the user query with the same HF embedding model
- Retrieves context chunks from Chroma
- Rewrites the query to improve retrieval
- Merges original-query and rewritten-query results
- Re-ranks the retrieved chunks with Ollama
- Builds the final grounded prompt
- Generates the final answer

### `app_ollama_HF.py`
- Gradio chat interface for interactive RAG usage

### `evaluation/test_ollama_HF.py`
- Defines the test schema
- Loads the evaluation dataset

### `evaluation/eval_ollama_HF.py`
- Runs retrieval evaluation
- Runs answer evaluation
- Uses one model to answer and another model to judge

### `evaluation/tuner_ollama_HF.py`
- Tries multiple `RETRIEVAL_K` / `FINAL_K` combinations
- Uses stratified folds by category
- Computes a weighted global `score`
- Saves all candidates to `evaluation/results_ollama_HF/tuning_results.jsonl`

### `evaluator_ollama_HF.py`
- Gradio dashboard for full evaluation
- Shows retrieval metrics
- Shows answer metrics
- Shows per-category charts

## End-to-End Pipeline
1. `ingest_ollama_HF.py` builds the vector database.
2. `answer_ollama_HF.py` performs retrieval, rerank, and final answer generation.
3. `app_ollama_HF.py` exposes the chat interface.
4. `eval_ollama_HF.py` measures retrieval and answer quality.
5. `tuner_ollama_HF.py` searches for the best retrieval settings.
6. `evaluator_ollama_HF.py` shows aggregate evaluation results in a dashboard.

## Current Main Parameters

### Ingestion
- File: `pro_implementation/ingest_ollama_HF.py`
- Chunking model: `ollama/qwen2.5:7b-instruct`
- Embedding model: `intfloat/multilingual-e5-base`
- Average chunk size: `300`
- Workers: `2`
- Vector DB path: `week5/preprocessed_db`
- Collection name: `docs`

### Retrieval / Answering
- File: `pro_implementation/answer_ollama_HF.py`
- Generation / rewrite / rerank model: `ollama/qwen2.5:7b-instruct`
- Embedding model: `intfloat/multilingual-e5-base`
- Retrieval depth: `RETRIEVAL_K = 12`
- Final context size: `FINAL_K = 6`

### Evaluation
- File: `evaluation/eval_ollama_HF.py`
- Generation model: local Ollama model from that file
- Judge model: local Ollama model from that file

## Performance-Critical Parameters

1. **Embedding model**
- What it affects: semantic retrieval quality
- Where to change: `pro_implementation/ingest_ollama_HF.py` and `pro_implementation/answer_ollama_HF.py`
- Important: both files must match, then re-ingest

2. **Average chunk size**
- What it affects: retrieval granularity vs context continuity
- Where to change: `pro_implementation/ingest_ollama_HF.py`
- Important: re-ingest after changing it

3. **Retrieval depth**
- What it affects: how many raw chunks enter the rerank step
- Where to change: `pro_implementation/answer_ollama_HF.py`
- Parameter: `RETRIEVAL_K`

4. **Final context size**
- What it affects: how many reranked chunks are finally passed to the answer model
- Where to change: `pro_implementation/answer_ollama_HF.py`
- Parameter: `FINAL_K`

5. **Query rewrite quality**
- What it affects: whether the second retrieval pass finds better chunks
- Where to change: `pro_implementation/answer_ollama_HF.py`
- Function: `rewrite_query()`

6. **Rerank quality**
- What it affects: whether the most useful chunks survive into final context
- Where to change: `pro_implementation/answer_ollama_HF.py`
- Function: `rerank()`

7. **Evaluation models**
- What it affects: answer scores and judge strictness
- Where to change: `evaluation/eval_ollama_HF.py`

8. **Test dataset**
- What it affects: final reported metrics
- Where to change: `evaluation/tests.jsonl`

## Tuner Objective
The tuner combines:

- Retrieval metrics:
  - `mrr`
  - `ndcg`
  - `coverage`
- Answer metrics:
  - `accuracy`
  - `completeness`
  - `relevance`

It computes:

- `score`: weighted global objective
- `loss = 1 - score`

## Recommended Workflow
1. Change one important variable at a time.
2. If you changed chunking or embeddings, re-run ingestion.
3. Run the tuner to compare `RETRIEVAL_K` and `FINAL_K`.
4. Fix the best values in `answer_ollama_HF.py`.
5. Run `evaluator_ollama_HF.py` for full validation.

## Execution Commands

### Ingestion
```powershell
cd .\week5\pro_implementation
uv run ingest_ollama_HF.py
```

### Tuning
```powershell
cd ..\evaluation
uv run tuner_ollama_HF.py
```

### Full evaluation dashboard
```powershell
cd ..\
uv run evaluator_ollama_HF.py
```

### Chat app
```powershell
cd .\
uv run app_ollama_HF.py
```

## Quick Map
- Chunking and embeddings: `pro_implementation/ingest_ollama_HF.py`
- Retrieval and final answer: `pro_implementation/answer_ollama_HF.py`
- Chat UI: `app_ollama_HF.py`
- Evaluation logic: `evaluation/eval_ollama_HF.py`
- Test loader: `evaluation/test_ollama_HF.py`
- Tuning loop: `evaluation/tuner_ollama_HF.py`
- Evaluation dashboard: `evaluator_ollama_HF.py`
