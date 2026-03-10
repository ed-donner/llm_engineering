# Eval README (`*2.py` Pipeline)

## Performance-Critical Parameters
If you evaluate through `evaluator2.py`, these are the main knobs that change results the most:

1. **Retrieval `top_k`**
- **What it affects:** context breadth
- **Where to change:** `implementation/answer2.py`
- **Parameter:** `RETRIEVAL_K = ...`

2. **Chunking strategy**
- **What it affects:** retrieval granularity and context continuity
- **Where to change:** `implementation/ingest2.py`
- **Important:** re-run ingestion after changing chunking.

3. **Embedding model**
- **What it affects:** semantic matching quality in vector search
- **Where to change:** `implementation/ingest2.py` and `implementation/answer2.py`
- **Important:** the model must match in both files, then re-ingest.

4. **Generation model**
- **What it affects:** answer quality
- **Where to change:** `evaluation/eval2.py`
- **Parameter:** `GENERATION_MODEL = "..."`

5. **Judge model**
- **What it affects:** scoring strictness and consistency
- **Where to change:** `evaluation/eval2.py`
- **Parameter:** `JUDGE_MODEL = "..."`

6. **Prompt strictness**
- **What it affects:** hallucination control and relevance
- **Where to change:** `implementation/answer2.py`
- **Parameter block:** `SYSTEM_PROMPT`

7. **Evaluation dataset quality**
- **What it affects:** final scores
- **Where to change:** `evaluation/tests.jsonl`

## What Each `*2.py` File Does

### `implementation/ingest2.py`
- Loads markdown docs from `knowledge-base/`.
- Splits docs into chunks.
- Creates embeddings and writes vectors to Chroma.

### `implementation/answer2.py`
- Opens the vector DB.
- Retrieves top-k context chunks.
- Builds the prompt with grounded context.
- Generates the answer.

### `app2.py`
- Gradio UI for interactive chat.
- Shows answer and retrieved context side-by-side.

### `evaluation/test2.py`
- Defines the `TestQuestion` schema.
- Loads and validates rows from `tests.jsonl`.

### `evaluation/eval2.py`
- Runs retrieval evaluation: MRR, nDCG, keyword coverage.
- Runs answer evaluation: accuracy, completeness, relevance.
- Uses separate generation and judge models.

### `evaluator2.py`
- Gradio dashboard for the full evaluation flow.
- Displays aggregate metric cards and category charts.

## Evaluation Order
1. `evaluator2.py` starts the UI.
2. It calls `evaluation/eval2.py`.
3. `eval2.py` loads tests via `evaluation/test2.py`.
4. Retrieval uses `fetch_context()` from `implementation/answer2.py`.
5. Answering uses `answer_question()` from `implementation/answer2.py`, then the judge scores it.

## Recommended Workflow
1. Change one parameter at a time.
2. Re-run ingestion if you changed chunking or embeddings.
3. Run `python evaluator2.py`.
4. Compare retrieval and answer metrics.

## Quick Map
- Retrieval depth: `answer2.py -> RETRIEVAL_K`
- Chunking: `ingest2.py`
- Embeddings: `ingest2.py` + `answer2.py`
- Generator model: `eval2.py -> GENERATION_MODEL`
- Judge model: `eval2.py -> JUDGE_MODEL`
- Prompt grounding: `answer2.py -> SYSTEM_PROMPT`
- Test definitions: `evaluation/tests.jsonl`
