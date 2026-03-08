# Week 5 Community Contribution: Curriculum Hybrid RAG Assistant

This project is a practical Week 5 capstone that combines ideas from Weeks 1-5:

- Week 1: prompt discipline, context handling, and cost-aware model use
- Week 2: tool-oriented workflow and optional Gradio interface
- Week 3: answer quality auditing with structured scoring
- Week 4: iterative agent loop that can refine weak answers
- Week 5: retrieval augmented generation (RAG) with embeddings and citations

## What this project does

`curriculum_hybrid_rag.py` builds and serves a local hybrid retrieval assistant over markdown/text files.

It supports:

- ingestion and chunking of local knowledge files
- embedding index creation and local persistence
- hybrid retrieval (vector similarity + keyword overlap)
- citation-aware answer generation
- structured answer evaluation (`groundedness`, `completeness`, `citation_quality`)
- iterative refinement loop when evaluation scores are low
- CLI chat mode and optional Gradio chat UI

## Folder structure

- `curriculum_hybrid_rag.py` - main script for indexing, ask, chat, and UI
- `week5_curriculum_hybrid_rag.ipynb` - notebook runner with setup/import/index/ask flow
- `requirements.txt` - minimal Python dependencies
- `.env.example` - copy to `.env` and add your key
- `artifacts/` - generated index metadata and embeddings (created at runtime)

## Setup

From repo root:

```bash
pip install -r week5/community-contributions/BernardUdo/week5-curriculum-hybrid-rag/requirements.txt
```

Set your API key in `.env` (OpenRouter recommended):

```bash
OPENROUTER_API_KEY=your_key_here
# optional:
# OPENROUTER_SITE_URL=http://localhost
# OPENROUTER_APP_NAME=week5-curriculum-hybrid-rag
```

Fallback is supported:

```bash
OPENAI_API_KEY=your_key_here
```

## Usage

### 1) Build index

```bash
python week5/community-contributions/BernardUdo/week5-curriculum-hybrid-rag/curriculum_hybrid_rag.py \
  --source-dir week5/knowledge-base index
```

### 2) Ask one question

```bash
python week5/community-contributions/BernardUdo/week5-curriculum-hybrid-rag/curriculum_hybrid_rag.py ask \
  --question "Who founded Insurellm and when?"
```

### 3) Interactive CLI chat

```bash
python week5/community-contributions/BernardUdo/week5-curriculum-hybrid-rag/curriculum_hybrid_rag.py chat
```

### 4) Optional Gradio app

```bash
python week5/community-contributions/BernardUdo/week5-curriculum-hybrid-rag/curriculum_hybrid_rag.py ui
```

## Notes

- This project uses OpenRouter via the OpenAI-compatible client (`https://openrouter.ai/api/v1`).
- API key lookup order is `OPENROUTER_API_KEY` then `OPENAI_API_KEY`.
- Default models are `openai/gpt-4.1-mini` (answering), `openai/gpt-4.1-nano` (evaluation), and `openai/text-embedding-3-small` (embeddings).
- Retrieved sources are included in answers as citations like `[contracts/file.md#c12]`.
- If evaluation detects weak grounding/completeness/citations, the assistant retries with expanded retrieval.
