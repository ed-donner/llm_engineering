# Week 5 Assignment: Personal Knowledge Worker

## Overview
This notebook implements an end-to-end conversational RAG workflow over a personal knowledge base, including document ingestion, chunking, vectorization, retrieval, reranking, QA, and Gradio UI.

## Features
- Document ingestion from local folders (.md and .txt) with support for typed subfolders
- LLM-based intelligent chunking with structured outputs (headline, summary, original text)
- ChromaDB vector store creation with OpenAI embeddings and collection rebuild
- Advanced retrieval pipeline: query rewriting, semantic retrieval, LLM reranking
- Conversational QA with source-aware context and history-aware response
- Gradio chat interface for interactive usage
- Notebook test step for quick sanity checks

## Technical Details
- Structured notebook flow: setup → ingestion → chunking → vectorization → retrieval/rerank → QA → UI launch
- Compatible with installed Gradio version

## Requirements
- Python packages: gradio, chromadb, openai, python-dotenv
- OpenAI API key set in environment

## Setup
1. Install dependencies:
   ```bash
   pip install gradio chromadb openai python-dotenv
   ```
2. Set up OpenAI API key in `.env`:
   ```env
   OPENAI_API_KEY=your_openai_key_here
   ```
3. Run the notebook

## Usage
- Ingest documents from a local folder
- Chunk documents with LLM
- Create ChromaDB collection
- Use Gradio chat interface for QA
- Run notebook test step for validation

## Limitations
- Only .md and .txt files supported
- Relies on LLM quality for chunking and QA
- Requires OpenAI API key

## Conclusion
This notebook provides a robust, modular workflow for building a personal knowledge worker with conversational RAG capabilities.
