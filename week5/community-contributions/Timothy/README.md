# Developer Documentation RAG Assistant

## Overview

This project is a Retrieval-Augmented Generation (RAG) assistant that answers developer questions using official documentation from LangChain, HuggingFace, FastAPI, and Python. It consists of two main components:

- **kb_crawler**: Crawls and extracts documentation from multiple sources, saving them as Markdown files in a structured knowledge base.
- **RAG Assistant Notebook**: Loads, chunks, embeds, and indexes the documentation, then provides a chat interface for answering questions using a language model and document retrieval.

## Workflow

1. **Crawl Documentation**
   - Run `kb_crawler/crawl_docs.py` to download and convert documentation from supported sites into Markdown files, organized in the `knowledge_base` directory.

2. **Ingest and Index**
   - The notebook loads all Markdown files, splits them into chunks, and generates vector embeddings using HuggingFace models.
   - ChromaDB is used to store and index the embeddings for fast similarity search.

3. **Question Answering**
   - User questions are processed via a Gradio chat UI.
   - The system retrieves the most relevant documentation chunks and uses an LLM (via OpenRouter) to generate accurate, context-grounded answers.

## Requirements

Install dependencies with:
```
pip install -r requirements.txt
```
Main requirements:
- requests, beautifulsoup4, html2text, trafilatura, lxml, tqdm
- langchain, chromadb, huggingface, gradio, openai

## Usage

1. **Crawl Docs**  
   ```
   python kb_crawler/crawl_docs.py
   ```
2. **Run Notebook**  
   Open and run all cells in `week5-Exercise.ipynb` to build the vector store and launch the chat UI.

3. **Ask Questions**  
   Use the Gradio interface to ask questions about LangChain, HuggingFace, FastAPI, or Python documentation.

## Project Structure

- `kb_crawler/` — Documentation crawler script
- `knowledge_base/` — Crawled and processed docs (auto-generated)
- `week5-Exercise.ipynb` — Main RAG assistant notebook
- `requirements.txt` — Python dependencies
