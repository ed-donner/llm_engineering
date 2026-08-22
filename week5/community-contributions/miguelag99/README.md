# PokeRAG

A Pokémon-flavored RAG pipeline, built as a drop-in replacement for the Insurellm example used elsewhere in this course. Data is pulled live from the official [PokeAPI](https://pokeapi.co/docs/v2), chunked and embedded into a local vector store, and served through a retrieve-rerank-generate answering pipeline with its own retrieval + answer-quality evaluation harness.

## Contents

```
PokeRAG/
├── build_knowledge_base.py     # fetches data from PokeAPI, writes the markdown knowledge base
├── ingest.py                   # chunks the knowledge base with an LLM and embeds it into Chroma
├── answer.py                   # RAG answering: query rewrite, retrieval, rerank, generation
├── eval.py                     # evaluation logic (retrieval metrics + LLM-as-judge) + CLI for one test
├── evaluator.py                # Gradio dashboard to run evaluation over the whole test set
├── poke-knowledge-base/        # generated knowledge base (markdown, one file per entity)
│   ├── pokemon/                 # 151 files, Generation 1 (#1-151)
│   └── items/                   # 120 files, classic Generation 1 items
├── preprocessed_db/            # generated Chroma vector store (output of ingest.py)
└── evaluation/
    ├── test.py                  # TestQuestion schema + loader for poke_tests.jsonl
    ├── generate_tests.py        # parses the knowledge base, writes evaluation ground truth
    └── poke_tests.jsonl         # generated evaluation ground truth
```

`poke-knowledge-base/` mirrors the two-subfolder-per-doc-type layout used by `knowledge-base/` elsewhere in this course (`doc_type` = `pokemon` or `items`).

## Prerequisites

`ingest.py`, `answer.py`, and `eval.py` all call out to an **Ollama server** via `litellm`/`ollama` clients — no OpenAI key required, but you do need a reachable Ollama instance with the two models pulled:

- `gemma4:e4b` — chat/completion model (chunking, query rewriting, reranking, answer generation, LLM-as-judge)
- `qwen3-embedding:0.6b` — embedding model

Each script currently hardcodes `OLLAMA_SERVER_URL = "http://localhost:11434"` near the top — update it to point at your own Ollama server before running anything.

## Building the knowledge base

```bash
uv run PokeRAG/build_knowledge_base.py
```

For each Pokémon (`GET /pokemon/{id}`), it writes a markdown file with:
- Pokédex ID, type(s), height, weight, abilities (hidden abilities marked)
- Pokédex description(s) for Generation 1 games (`GET /pokemon-species/{id}`), showing the Red/Blue text and, when it differs, the Yellow text separately

For items, since PokeAPI doesn't tag items with a reliable Generation 1 flag (item `game_indices`/`flavor_text_entries` only start at Generation III, even for items that existed in Red/Blue/Yellow), the script uses a **hardcoded curated list** of ~120 classic Gen 1 item names (Poké Balls, medicine, vitamins, battle/X-items, evolution stones, key items, TM01-50, HM01-05). For each (`GET /item/{name}`), it writes a markdown file with category, cost (when available), attributes, effect, description, and localized names in other languages (French, German, Japanese, Korean, Chinese, etc., from the API's `names` field).

The script is polite to the public API (small delay between requests, no auth needed) and prints a warning + continues if any individual fetch fails, rather than aborting the whole run. Re-running it overwrites `poke-knowledge-base/` with fresh data from the API.

## Data ingestion

```bash
uv run PokeRAG/ingest.py
```

Loads every markdown file under `poke-knowledge-base/` (a homemade `DirectoryLoader`, using the subfolder name as `doc_type`), then for each document:

1. Sends it to the LLM (`gemma4:e4b` via Ollama) with a prompt asking it to split the document into overlapping chunks (~25% / ~50 words overlap), each with a `headline`, a `summary`, and the verbatim `original_text` — structured output via a Pydantic `Chunks` schema.
2. Embeds every chunk's `headline + summary + original_text` with the `qwen3-embedding:0.6b` model.
3. Writes ids, embeddings, documents, and `{source, type}` metadata into a Chroma collection named `docs`, persisted to `preprocessed_db/`.

Chunking runs through a `multiprocessing.Pool` (`WORKERS = 1` by default — raise it if your Ollama server can handle concurrent requests, or drop it back to 1 if you hit rate limits) with exponential-backoff retries. Re-running `ingest.py` drops and recreates the `docs` collection from scratch.

## Generating evaluation ground truth

```bash
uv run PokeRAG/evaluation/generate_tests.py
```

Parses the markdown files in `poke-knowledge-base/` (not hand-written facts) and derives test questions directly from that data, so reference answers stay accurate to whatever is actually in the knowledge base. Output (`evaluation/poke_tests.jsonl`) matches the `TestQuestion` schema in `evaluation/test.py`:

```json
{"question": "...", "keywords": [...], "reference_answer": "...", "category": "..."}
```

Categories covered:
- **direct_fact** – single-entity facts (type, height/weight, abilities, item category/cost)
- **numerical** – counts (number of types, Pokédex number)
- **comparative** – head-to-head comparisons (heavier/taller Pokémon, pricier item)
- **relationship** – groupings (shared abilities, type combinations, item categories)
- **spanning** – questions requiring two combined facts to answer
- **holistic** – aggregate stats across the whole dataset (heaviest/lightest, most common type, most expensive item, etc.)
- **temporal** – Red/Blue vs Yellow Pokédex description differences

## Evaluation

Two ways to run the evaluation suite defined in `evaluation/poke_tests.jsonl`, both combining:
- **Retrieval metrics** (`evaluate_retrieval`): Mean Reciprocal Rank and nDCG of each test's keywords against `fetch_context`'s retrieved chunks, plus keyword coverage %.
- **Answer quality** (`evaluate_answer`): runs the full RAG pipeline and has the LLM judge the generated answer against the reference answer on accuracy, completeness, and relevance (1-5 each).

**Single test, CLI:**

```bash
uv run PokeRAG/eval.py <test_row_number>
```

Prints the question, retrieval metrics, the generated answer, and the judge's feedback/scores for one row of `poke_tests.jsonl`.

**Full suite, Gradio dashboard:**

```bash
uv run PokeRAG/evaluator.py
```

Launches a browser dashboard with two sections — Retrieval Evaluation and Answer Evaluation — each with a "Run Evaluation" button that sweeps every test, showing color-coded summary metrics (MRR/nDCG/coverage or accuracy/completeness/relevance) and a bar chart of the average score per question category.

## Known caveats

- Pokémon data comes from the current `/pokemon/{id}` endpoint, which reflects present-day game data, not the original Gen 1 games. A few Gen 1 Pokémon that gained a secondary type in later generations (e.g. Mr. Mime → Psychic/Fairy) will show that modern typing rather than their original single type.
- PokeAPI recently replaced the flat `cost` field on items with a per-version-group `prices` list, which is only partially backfilled as of this writing. `build_knowledge_base.py` handles both shapes and simply omits the `Cost` line when no price data is available for an item, rather than failing. Re-running the script later, once PokeAPI's backfill completes, should recover cost data for more items.
