# Insurellm RAG Upgrade

Beginner-friendly documentation for a local Retrieval-Augmented Generation (RAG) project built around the fictional company **Insurellm**.

## Executive Summary

This project upgrades a basic company knowledge-base chatbot so it can answer a wider range of questions more reliably. Instead of relying only on chunk-level vector search, it adds higher-level retrieval layers such as **document summaries** and **global indexes**. These improvements help the system answer broad questions like "list all products" or "who won this award across all years" with better coverage.

The project also introduces a structured-data path for employee records. Employee profile markdown files can be converted into a JSONL dataset that is easier to inspect and eventually easier to compute over. The overall goal is to make the RAG system more accurate for beginner evaluation tasks while keeping the stack simple: local Python scripts, Chroma for vector storage, Gradio for UI, and LLM calls through OpenAI and LiteLLM.

## What This Project Includes

- A Gradio chat app for asking questions about Insurellm
- A retrieval and answer evaluation dashboard
- A chunk-based RAG pipeline backed by Chroma
- Document-level summaries for better broad retrieval
- Cross-document global indexes for holistic questions
- Employee record extraction into `structured/employees.jsonl`

## Current Implementation Status

The PRD includes both implemented work and planned work.

### Implemented

- Chunk-based ingestion into a `docs` Chroma collection
- Document summaries into a `doc_summaries` collection
- Global index documents into a `global_indexes` collection
- Holistic question routing in [`pro_implementation/answer.py`]
- Employee profile extraction into [`structured/employees.jsonl`]

## Tech Stack

Based on the PRD and current code:

| Area            | Tooling                                       |
| --------------- | --------------------------------------------- |
| Language        | Python                                        |
| UI              | Gradio                                        |
| Vector database | Chroma                                        |
| LLM calls       | LiteLLM, OpenAI SDK                           |
| Validation      | Pydantic                                      |
| Retry logic     | Tenacity                                      |
| Data formats    | Markdown, JSONL, Chroma persisted collections |

## Project Structure

```text
jsjasee_week5day5/
├── README.md
├── app.py
├── evaluator.py
├── pro_implementation/
│   ├── answer.py
│   └── ingest.py
├── evaluation/
│   ├── eval.py
│   ├── test.py
│   └── tests.jsonl
├── knowledge-base/
│   ├── company/
│   ├── contracts/
│   ├── employees/
│   └── products/
├── structured/
│   └── employees.jsonl
└── preprocessed_db/
```

## Architecture Overview

### High-Level Flow

```text
Knowledge Base Markdown Files
        |
        v
  Ingestion Pipeline
  - chunk documents
  - summarize each document
  - build global indexes
  - extract employee records
        |
        +---------------------> Chroma: docs
        |
        +---------------------> Chroma: doc_summaries
        |
        +---------------------> Chroma: global_indexes
        |
        +---------------------> JSONL: structured/employees.jsonl

User Question
        |
        v
  Query Router
  - normal question -> chunk retrieval
  - holistic question -> global indexes + doc summaries + source chunks
        |
        v
  Re-ranking
        |
        v
  LLM Answer Generation
        |
        v
  Gradio Chat UI
```

### Main Components

#### 1. Ingestion

[`pro_implementation/ingest.py`]

It defines:

- `Chunk` and `Chunks` for chunked knowledge-base content
- `DocumentSummary` for one summary per source document
- `GlobalIndexDoc` for cross-document indexes
- `EmployeeRecord` for structured employee data

#### 2. Retrieval

[`pro_implementation/answer.py`]

It supports two retrieval paths:

- **Normal retrieval** for direct fact questions
- **Holistic retrieval** for broad questions containing phrases like `all`, `every`, `overview`, or `across`

#### 3. User Interface

[`app.py`]

#### 4. Evaluation

- `evaluator.py` launches a Gradio dashboard
- `evaluation/eval.py` runs retrieval and answer scoring
- `evaluation/tests.jsonl` stores the evaluation questions

### PRD Improvements Reflected in the Code

| Improvement                                       | Why it matters                                                | Status in code      |
| ------------------------------------------------- | ------------------------------------------------------------- | ------------------- |
| Document summary collection                       | Improves document-level retrieval for broad queries           | Implemented         |
| Global index documents                            | Helps answer cross-document questions                         | Implemented         |
| Holistic question retrieval path                  | Routes broad questions through index and summary layers first | Implemented         |
| Employee structured records                       | Prepares data for exact filtering and computation             | Implemented         |
| Structured QA path for salary/tenure calculations | Would avoid LLM guessing for arithmetic questions             | Not yet implemented |

## Setup Guide

### Prerequisites

Install the following first:

- Python 3.10+
- An OpenAI API key for embeddings
- An LLM provider key for the completion model you use

The current code uses:

- OpenAI embeddings: `text-embedding-3-large`
- LiteLLM completion models such as `openai/gpt-4.1-nano` and `openrouter/openai/gpt-oss-120b`

### 1. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

This project does not currently include a local `requirements.txt`, so install the packages used by the code directly:

```bash
pip install gradio python-dotenv pandas pydantic chromadb openai litellm tenacity tqdm
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```dotenv
OPENAI_API_KEY=your_openai_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

Notes:

- `OPENAI_API_KEY` is required for embeddings through the OpenAI SDK.
- `OPENROUTER_API_KEY` is needed only if you keep the default answer model in `pro_implementation/answer.py`.
- If you switch all models to OpenAI-only models, you may not need the OpenRouter key.

### 4. Confirm the Knowledge Base Exists

The project expects markdown files under `knowledge-base/`.

Current folders:

- `company`
- `contracts`
- `employees`
- `products`

## Running the Project

### Run the Chat App

```bash
python app.py
```

This opens a Gradio chat UI in your browser.

### Run the Evaluation Dashboard

```bash
python evaluator.py
```

This opens a Gradio dashboard with:

- retrieval evaluation
- answer evaluation
- category-level charts

### Run One CLI Evaluation Test

```bash
python evaluation/eval.py 0
```

Replace `0` with the row number from `evaluation/tests.jsonl`.

## Ingestion Guide

### Important Current Behavior

The ingestion code supports several outputs, but the script entrypoint currently only runs employee record extraction by default.

In `pro_implementation/ingest.py`, the following steps exist in code but are commented out inside `if __name__ == "__main__":`

- chunk generation
- document summary generation
- global index generation
- vector embedding writes for those collections

That means a beginner should understand two things:

1. The codebase supports the full upgraded pipeline.
2. The default script entrypoint does not currently run the full pipeline automatically.

### Generate Employee Records

```bash
python pro_implementation/ingest.py
```

This writes employee records to:

- `structured/employees.jsonl`

### Generate Chunks, Summaries, and Global Indexes

To populate the full retrieval pipeline, enable the commented sections in `pro_implementation/ingest.py` under the `__main__` block, then run:

```bash
python pro_implementation/ingest.py
```

The intended outputs are:

| Output             | Storage                             |
| ------------------ | ----------------------------------- |
| document chunks    | Chroma collection: `docs`           |
| document summaries | Chroma collection: `doc_summaries`  |
| global indexes     | Chroma collection: `global_indexes` |
| employee records   | `structured/employees.jsonl`        |

## Usage Guide

### Ask Questions in the Chat UI

Example questions:

```text
What is Claimllm?
```

```text
Who are all the winners of the Insurellm Innovator of the Year award across all years?
```

```text
Which products does Insurellm offer?
```

### How Question Routing Works

- Direct fact questions usually go through standard chunk retrieval.
- Broad questions with phrases like `all`, `every`, `overview`, or `across` use the holistic retrieval path.
- Retrieved results are reranked before the final answer is generated.

### What You See in the UI

The chat app shows:

- the conversation on the left
- retrieved context on the right

This makes it easier for new developers to inspect whether the model is using the right source material.

### Evaluation Workflow

Use the evaluation tools when you want to measure:

- retrieval quality
- answer quality
- per-category performance

The retrieval evaluation reports metrics such as:

- MRR
- nDCG
- keyword coverage

The answer evaluation reports:

- accuracy
- completeness
- relevance

## Configuration

### Key Paths

| Setting                    | Current value                |
| -------------------------- | ---------------------------- |
| Knowledge base root        | `knowledge-base/`            |
| Vector DB path             | `preprocessed_db/`           |
| Structured employee output | `structured/employees.jsonl` |

### Models Used in Code

| File                           | Purpose                                           | Current model                    |
| ------------------------------ | ------------------------------------------------- | -------------------------------- |
| `pro_implementation/ingest.py` | chunking, summaries, indexes, employee extraction | `openai/gpt-4.1-nano`            |
| `pro_implementation/answer.py` | answer generation, query rewriting, reranking     | `openrouter/openai/gpt-oss-120b` |
| embeddings                     | vector search                                     | `text-embedding-3-large`         |

If you want to simplify setup, you can standardize these models to one provider before running the project.

### Secrets Handling

Recommended approach:

- Keep API keys in a local `.env` file
- Do not hardcode secrets in Python files
- Do not commit `.env` files to version control

Example:

```dotenv
OPENAI_API_KEY=your_openai_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Known Limitations

- `structured/employees.jsonl` is empty until you generate it
