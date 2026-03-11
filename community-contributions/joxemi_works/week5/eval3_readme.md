# Eval README (`*3.py` Pipeline)

## Performance-Critical Parameters
If you evaluate through `evaluator3.py`, these are the main knobs that change results the most:

1. **Retrieval `top_k`**
- **What it affects:** context breadth and noise level
- **Where to change:** `pro_implementation/answer3.py`
- **Parameter:** `RETRIEVAL_K = ...`

2. **Chunking strategy**
- **What it affects:** retrieval granularity and chunk relevance
- **Where to change:** `pro_implementation/ingest3.py`
- **Parameters:** `AVERAGE_CHUNK_SIZE`, chunking prompt
- **Important:** re-run ingestion after changing chunking.

3. **Embedding model**
- **What it affects:** semantic matching quality in vector search
- **Where to change:** `pro_implementation/ingest3.py` and `pro_implementation/answer3.py`
- **Parameter:** `embedding_model = "intfloat/multilingual-e5-base"`
- **Important:** it must match in both files, then re-ingest.

4. **Generation model**
- **What it affects:** answer quality
- **Where to change:** `evaluation/eval3.py`
- **Parameter:** `GENERATION_MODEL = "qwen2.5:7b-instruct"`

5. **Judge model**
- **What it affects:** scoring strictness and consistency
- **Where to change:** `evaluation/eval3.py`
- **Parameter:** `JUDGE_MODEL = "llama3.1:8b"`

6. **Local Ollama generation**
- **What it affects:** latency, throughput and hardware pressure
- **Where to change:** `pro_implementation/ingest3.py` and `pro_implementation/answer3.py`
- **Parameter:** `MODEL = "ollama/qwen2.5:7b-instruct"`

7. **Parallel ingestion workers**
- **What it affects:** ingestion speed and local resource usage
- **Where to change:** `pro_implementation/ingest3.py`
- **Parameter:** `WORKERS = ...`

8. **Prompt strictness**
- **What it affects:** grounding, hallucinations and relevance
- **Where to change:** `pro_implementation/answer3.py`
- **Parameter block:** `SYSTEM_PROMPT`, `rewrite_query()`, `rerank()`

9. **Evaluation dataset quality**
- **What it affects:** final scores and what "good" means
- **Where to change:** `evaluation/tests.jsonl`

## What Each `*3.py` File Does

### `pro_implementation/ingest3.py`
- Loads markdown docs from `knowledge-base/`.
- Uses local Ollama to split documents into structured chunks.
- Uses Hugging Face embeddings via `HuggingFaceEmbeddings`.
- Writes vectors and metadata into Chroma.
- Supports parallel chunk generation with `WORKERS`.

### `pro_implementation/answer3.py`
- Opens the Chroma DB.
- Uses HF embeddings for query embedding.
- Retrieves top-k context chunks.
- Rewrites the query and reranks retrieved chunks with Ollama.
- Generates the final grounded answer with Ollama.
- Supports `model_name` override in `answer_question(..., model_name=...)`.

### `app3.py`
- Gradio UI for interactive chat.
- Calls `pro_implementation/answer3.py`.
- Shows answer and retrieved context side-by-side.

### `evaluation/test3.py`
- Defines the `TestQuestion` schema.
- Loads and validates rows from `tests.jsonl`.

### `evaluation/eval3.py`
- Runs retrieval evaluation: MRR, nDCG, keyword coverage.
- Runs answer evaluation: accuracy, completeness, relevance.
- Uses `qwen2.5:7b-instruct` as generation model.
- Uses a local Ollama judge model for scoring.

### `evaluator3.py`
- Gradio dashboard for the full evaluation flow.
- Displays aggregate metric cards and category charts.
- Reads runtime config from `eval3.py`, `answer3.py` and `ingest3.py`.

## Evaluation Order
1. `evaluator3.py` starts the UI.
2. It calls `evaluation/eval3.py`.
3. `eval3.py` loads tests via `evaluation/test3.py`.
4. Retrieval uses `fetch_context()` from `pro_implementation/answer3.py`.
5. Answering uses `answer_question()` from `pro_implementation/answer3.py`.
6. The local judge model scores the generated answer.

## Recommended Workflow
1. Change one parameter at a time.
2. Re-run ingestion if you changed chunking, embeddings, or the vector DB build.
3. Run `python pro_implementation/ingest3.py`.
4. Run `python evaluator3.py`.
5. Compare retrieval and answer metrics.

## Quick Map
- Retrieval depth: `answer3.py -> RETRIEVAL_K`
- Chunking and worker count: `ingest3.py -> AVERAGE_CHUNK_SIZE`, `WORKERS`
- Embeddings: `ingest3.py` + `answer3.py -> embedding_model`
- Generator model: `eval3.py -> GENERATION_MODEL`
- Judge model: `eval3.py -> JUDGE_MODEL`
- Ollama answer model: `ingest3.py` and `answer3.py -> MODEL`
- Prompt grounding: `answer3.py -> SYSTEM_PROMPT`
- Test definitions: `evaluation/tests.jsonl`
