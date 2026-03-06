# Nigerian Tax Expert Assistant

This is a Retrieval-Augmented Generation (RAG) system designed to act as an expert Nigerian Tax Consultant. It ingests PDF documents regarding tax reforms (CIT, PIT, VAT, WHT, etc.) and provides accurate, context-aware answers to user queries through a chat interface.

## Features

- **Specialized Knowledge Base**: Ingests tax documents (PDFs) and splits them into semantic chunks with headlines, summaries, and keywords.
- **Advanced RAG Pipeline**:
  - **Query Rewriting**: Refines user questions to improve retrieval accuracy using tax terminology.
  - **Hybrid Search**: Merges results from original and rewritten queries.
  - **Reranking**: Re-orders retrieved chunks based on relevance to the specific tax question.
- **Interactive UI**: A clean Gradio interface for chatting with the assistant and viewing retrieved context side-by-side.

## Prerequisites

- Python 3.10+
- API Keys:
  - **OpenAI API Key**: For embeddings (`text-embedding-3-large`).
  - **Groq API Key** (or OpenAI): For the LLM (`groq/openai/gpt-oss-120b` or similar).

## Setup

1. **Install Dependencies**:
   Ensure you have the required Python packages installed:
   ```bash
   pip install openai python-dotenv chromadb litellm pydantic tenacity tqdm langchain-docling gradio
   ```

2. **Environment Variables**:
   Create a `.env` file in the root directory and add your API keys:
   ```env
   OPENAI_API_KEY=sk-...
   GROQ_API_KEY=gsk_...
   ```

## Usage

### 1. Ingest Documents

Place your Nigerian tax PDF documents into a folder named `knowledge-base` in the project root.

Run the ingestion script to process documents and create the vector database:

```bash
python ingest.py
```

This script will:
- Load PDFs using `DoclingLoader`.
- Split text into semantic chunks using an LLM to identify rules, headlines, and keywords.
- Generate embeddings and store them in a local ChromaDB (`tax_db`).

### 2. Run the Chat Application

Start the Gradio web interface:

```bash
python app.py
```

Open the provided local URL (usually `http://127.0.0.1:7860`) in your browser. You can now ask questions like:
- "What is the current VAT rate?"
- "Explain the penalty for late filing of CIT."
- "What are the WHT rates for construction contracts?"
- "Who is exempt from Personal Income Tax?"