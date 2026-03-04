# Eval README (`*2.py` Pipeline)

## Performance-Critical Parameters (Read This First)
If you evaluate through `evaluator2.py`, these are the main knobs that change results the most:

1. **Retrieval `top_k`**
- **What it affects:** context breadth (too low misses facts, too high adds noise)
- **Where to change:** [answer2.py](/g:/joxemi_gimenez/000_enerlogix/udemy/projects/llm_engineering/week5/implementation/answer2.py)
- **Parameter:** `RETRIEVAL_K = ...`
- **Example:** `3 -> 5` often improves completeness; `5 -> 10` may reduce precision.

2. **Chunking strategy (`chunk_size`, `chunk_overlap`)**
- **What it affects:** retrieval granularity and context continuity
- **Where to change:** [ingest2.py](/g:/joxemi_gimenez/000_enerlogix/udemy/projects/llm_engineering/week5/implementation/ingest2.py)
- **Parameter location:** `RecursiveCharacterTextSplitter(chunk_size=..., chunk_overlap=...)`
- **Example:** `500/200 -> 700/150` can improve long-fact capture, but may dilute specificity.
- **Important:** re-run ingestion after changing chunking.

3. **Embedding model**
- **What it affects:** semantic matching quality in vector search
- **Where to change:** both [ingest2.py](/g:/joxemi_gimenez/000_enerlogix/udemy/projects/llm_engineering/week5/implementation/ingest2.py) and [answer2.py](/g:/joxemi_gimenez/000_enerlogix/udemy/projects/llm_engineering/week5/implementation/answer2.py)
- **Parameter:** `EMBEDDING_MODEL = "..."`
- **Example:** switching to a stronger embedding model may improve retrieval metrics.
- **Important:** model must match in both files; then re-ingest.

4. **Generation model (the model that answers)**
- **What it affects:** answer quality (`accuracy`, `completeness`, `relevance`)
- **Where to change:** [eval2.py](/g:/joxemi_gimenez/000_enerlogix/udemy/projects/llm_engineering/week5/evaluation/eval2.py)
- **Parameter:** `GENERATION_MODEL = "..."`
- **Example:** `phi3.5:latest` (faster) vs larger model (potentially better quality).

5. **Judge model (the model that scores answers)**
- **What it affects:** scoring strictness and consistency
- **Where to change:** [eval2.py](/g:/joxemi_gimenez/000_enerlogix/udemy/projects/llm_engineering/week5/evaluation/eval2.py)
- **Parameter:** `JUDGE_MODEL = "..."`
- **Example:** stronger judge model typically gives more reliable grading.

6. **Prompt strictness**
- **What it affects:** hallucination control and relevance
- **Where to change:** [answer2.py](/g:/joxemi_gimenez/000_enerlogix/udemy/projects/llm_engineering/week5/implementation/answer2.py)
- **Parameter block:** `SYSTEM_PROMPT`
- **Example:** stricter grounding instructions reduce invented facts but can reduce verbosity.

7. **Evaluation dataset quality**
- **What it affects:** final scores and what “good” means
- **Where to change:** [tests.jsonl](/g:/joxemi_gimenez/000_enerlogix/udemy/projects/llm_engineering/week5/evaluation/tests.jsonl)
- **Fields:** `question`, `keywords`, `reference_answer`, `category`
- **Example:** poor keywords/reference answers produce misleading metrics.

---

## What Each `*2.py` File Does

### [implementation/ingest2.py](/g:/joxemi_gimenez/000_enerlogix/udemy/projects/llm_engineering/week5/implementation/ingest2.py)
- Loads markdown docs from `knowledge-base/`.
- Adds `doc_type` metadata from folder names.
- Splits docs into chunks.
- Creates embeddings and writes vectors to `vector_db` (Chroma).
- Debug logging included (`DEBUG`, `dbg`).

### [implementation/answer2.py](/g:/joxemi_gimenez/000_enerlogix/udemy/projects/llm_engineering/week5/implementation/answer2.py)
- Opens `vector_db`.
- Retrieves top-k context chunks.
- Builds system prompt with retrieved context.
- Calls Ollama chat model to generate final answer.
- Supports optional model override in `answer_question(..., model_name=...)`.
- Includes terminal chat mode and debug logs.

### [app2.py](/g:/joxemi_gimenez/000_enerlogix/udemy/projects/llm_engineering/week5/app2.py)
- Gradio UI for interactive chat.
- Sends user messages to `answer2.py`.
- Shows answer and retrieved context side-by-side.
- Debug logging included.

### [evaluation/test2.py](/g:/joxemi_gimenez/000_enerlogix/udemy/projects/llm_engineering/week5/evaluation/test2.py)
- Defines the `TestQuestion` schema.
- Loads and validates test rows from `tests.jsonl`.
- Debug logging included.

### [evaluation/eval2.py](/g:/joxemi_gimenez/000_enerlogix/udemy/projects/llm_engineering/week5/evaluation/eval2.py)
- Runs retrieval evaluation metrics:
  - MRR
  - nDCG
  - keyword coverage
- Runs answer evaluation with LLM-as-a-judge:
  - accuracy
  - completeness
  - relevance
- Uses separate models:
  - `GENERATION_MODEL` (answering)
  - `JUDGE_MODEL` (grading)
- Debug logging included.

### [evaluator2.py](/g:/joxemi_gimenez/000_enerlogix/udemy/projects/llm_engineering/week5/evaluator2.py)
- Gradio dashboard for full evaluation flow.
- Runs retrieval and answer evaluation buttons.
- Displays aggregate metric cards and category bar charts.
- Reads and displays current generation/judge models from `eval2.py`.

---

## Evaluation Order When Running `evaluator2.py`
1. UI starts (`evaluator2.py`).
2. On button click, it calls `eval2.py`.
3. `eval2.py` loads tests via `test2.py`.
4. Retrieval path uses `fetch_context()` from `answer2.py`.
5. Answer path uses `answer_question()` from `answer2.py`, then judge scoring.
6. `evaluator2.py` aggregates and renders final cards/charts.

---

## Recommended Tuning Workflow
1. Change **one parameter at a time**.
2. If you changed embedding/chunking, run ingestion again:
   - `python implementation/ingest2.py`
3. Run evaluation dashboard:
   - `python evaluator2.py`
4. Compare:
   - Retrieval: MRR, nDCG, coverage
   - Answer: accuracy, completeness, relevance
5. Keep only changes that improve your target metric(s) without harming others.

---

## Quick “Where to Edit” Map
- Retrieval depth: `answer2.py -> RETRIEVAL_K`
- Chunking: `ingest2.py -> RecursiveCharacterTextSplitter(...)`
- Embeddings: `ingest2.py` + `answer2.py -> EMBEDDING_MODEL`
- Generator model: `eval2.py -> GENERATION_MODEL`
- Judge model: `eval2.py -> JUDGE_MODEL`
- Grounding behavior: `answer2.py -> SYSTEM_PROMPT`
- Test definitions: `evaluation/tests.jsonl`
