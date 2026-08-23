# AiForAll Assistant Exercise

This folder contains a Retrieval-Augmented Generation (RAG) demo for an AiForAll question-answering assistant.

## Overview

- `app.py` launches a Gradio web UI for chat-based questions.
- `answer.py` fetches relevant context from the knowledge base and generates a response using a large language model.
- `ingestion.py` ingests markdown documents from `docs/`, chunks them, embeds them, and stores the embeddings in `preprocessed_db`.
- `crawler.py` crawls documentation sites and saves markdown content into `docs/` for ingestion.
- `eval.py` evaluates generated answers across metrics like retrieval relevance, faithfulness, completeness, and answer relevance.
- `prompts.py` stores evaluation system prompts used by judge modules.
- `docs/` contains the knowledge base documents used for retrieval.
- `preprocessed_db/` stores the Chroma embedding database.

## Requirements

This project depends on the following Python libraries (at minimum):

- `gradio`
- `matplotlib`
- `python-dotenv`
- `langchain`
- `langchain_community`
- `langchain_chroma`
- `langchain_openai`
- `chromadb`
- `openai`
- `litellm`
- `pydantic`
- `tenacity`

Install the required packages in the repository environment before running the project:

```bash
uv sync
```

## Setup

1. Create a `.env` file in this folder or the repo root with your OpenAI credentials.

```env
OPENAI_API_KEY=your_openai_api_key
```

2. Activate your Python environment.

3. Crawl the target documentation sites into `docs/`:

```bash
uv run community-contributions\ashutosh\Week5\excercise\crawler.py
```

4. Ingest the crawled documents into the vector database:

```bash
uv run community-contributions\ashutosh\Week5\excercise\ingestion.py
```

This builds the vector database in `preprocessed_db/`.

## Run the Chat App

Start the assistant UI with:

```bash
uv run community-contributions\ashutosh\Week5\excercise\app.py
```

The Gradio interface will open in your browser. Enter questions about AiForAll and view:

- generated responses
- retrieved context
- evaluation metrics

## Notes

- `ingestion.py` uses the files under `docs/` as the source knowledge base.
- `answer.py` performs retrieval, reranking, and prompt construction to answer questions.
- `eval.py` uses judge modules in `judges/` to score responses.
- If `preprocessed_db/` already exists, you can skip ingestion unless you update `docs/`.

## Troubleshooting

- If the app cannot find embeddings, rerun `python ingestion.py`.
- If the model fails, verify `OPENAI_API_KEY` is set correctly.
- If the UI does not launch, confirm required libraries are installed.
