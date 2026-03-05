# Pharma-Aware RAG Pipeline

> [!IMPORTANT]
> **API Key Required**: This project requires an `OPENAI_API_KEY` for both Summary Generation (GPT-4o-mini) and Retrieval (Embeddings).

A high-precision Retrieval-Augmented Generation (RAG) pipeline specifically engineered for pharmaceutical data. This system transforms flat, unstructured medical PDFs/JSONs into a compliance-grade knowledge base by preserving medical context.

## The Core Engineering "Twists"

Standard RAG often fails in medical contexts because character-based chunking separates crucial warnings from their drug subjects. This pipeline solves that using:

1.  **Semantic Chunking**: Instead of character counts, we split text by **Medical Sections** (e.g., ADVERSE REACTIONS, CONTRAINDICATIONS).
2.  **Parent-Child Retrieval (Summary Vectors)**:
    -   We generate concise, strict summaries for every chunk.
    -   We **Index the Summary** for high-precision semantic search (avoiding "concept bleeding" between sections).
    -   We **Retrieve the Raw Content** from metadata to ensure the LLM generates answers based on the full clinical text.

##  Tech Stack

-   **Data**: OpenFDA API (Drug Labels)
-   **Vector DB**: ChromaDB (with OpenAI Embeddings)
-   **Orchestration**: Python (Strictly raw implementation, no generic frameworks like LangChain)
-   **LLM**: OpenAI (GPT-4o-mini)
-   **UI**: Gradio
-   **Environment**: `uv` for lightning-fast dependency management

##  Project Structure

```text
rx-research/
├── data/
│   ├── raw/             # Drug label JSONs (from OpenFDA or your source)
│   └── chroma_db/       # ChromaDB index (created by ingest; not in repo)
├── src/
│   ├── ingestion/       # data_loader.py, ingest.py
│   ├── processing/     # chunker.py, summarizer.py
│   ├── retrieval/      # vector_store.py
│   └── app.py           # Gradio Interface
├── main.py              # Entry point: launches app
├── benchmark.py         # Validation script
└── pyproject.toml
```

##  Setup & Installation

1.  **Environment Setup** (from this folder):
    ```bash
    uv sync
    ```

2.  **API Keys**:
    Create a `.env` file in this folder:
    ```text
    OPENAI_API_KEY=sk-your-key-here
    ```

##  Usage

### 1. Ingest data and build ChromaDB (required before first run)

ChromaDB is not in the repo; you create it locally from raw data.

**Download raw labels from OpenFDA , then ingest:**
```bash
# From the project folder (week5/community-contributions/codypharm)
uv run python -m src.ingestion.data_loader
uv run python -m src.ingestion.ingest
```

- **`data_loader`** downloads drug label JSONs from the OpenFDA API into `data/raw/`.
- **`ingest`** reads `data/raw/*.json`, chunks by medical section, summarizes chunks, and builds the vector index at `data/chroma_db/`.

### 2. Validation
Verify retrieval accuracy:
```bash
uv run python benchmark.py
```

### 3. Launch the UI
```bash
uv run python main.py
```
Access at `http://localhost:7861`.

## 🧪 Ground Truth Validation
Current benchmark questions cover:
- Detailed Dosing for Mekinist
- Differentiating Indications vs. Contraindications
- Boxed Warnings for Naproxen
- Specific allergen contraindications (Sulfonamides)
- Cardiovascular event incidence in Varenicline trials

---
*Disclaimer: Developed as a Compliance-Grade Engineering Demo. Always verify medical information with professional sources.*
