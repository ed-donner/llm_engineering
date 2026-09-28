# TMAY Chatbot

**TMAY** ("Tell Me About Yourself") is a RAG chatbot that answers job-interview-style questions about a person (work experience, education, stories, LinkedIn, GitHub, website, ...) using a personal knowledge base as its only source of truth.

The full project lives in its own repository:

👉 **https://github.com/seba3c/tmay_chatbot**

## What it includes

- An ingestion pipeline that chunks a Markdown knowledge base and embeds it into a Chroma vector DB.
- Two chatbot implementations to compare approaches:
  - **v1** – basic RAG (recursive text splitting, top-k retrieval).
  - **v2** – advanced RAG (LLM-based chunking, query rewriting, merged retrieval and LLM reranking).
- A Gradio chatbot UI, a Gradio evaluation dashboard, a CLI evaluator and a Plotly embedding visualizer.
- An evaluation suite with questions, keywords and reference answers.

Built as an extension of the Week 5 RAG lab of this course. The code is based on the labs in this repo, but restructured in a more object-oriented style (classes and modules instead of notebook-style functions and scripts).

Author: Sebastian Castañeda
