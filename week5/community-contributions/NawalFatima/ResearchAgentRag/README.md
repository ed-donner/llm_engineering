# Research RAG

A modular RAG system for research papers with hybrid retrieval, equation-aware chunking, and dual ingestion tiers.

---

## Architecture

```
PDF → Smart Processor → Chunker → Enrichment → ChromaDB
                                               ↓
Query → Rewrite (accurate) → Hybrid Retrieval → RRF Merge → Rerank → Answer
```

---

## Retrieval

### Hybrid Search
Combines dense vector search with BM25 keyword search, merged using **Reciprocal Rank Fusion (RRF)**. Chunks found by both systems rank highest — ensures exact matches (model names, BLEU scores, equations, figure references) aren't buried by semantic noise.

```
vector search (semantic)  ─┐
                            ├→ RRF merge → top-k chunks → answer
BM25 search (keyword)     ─┘
```

### Fast Mode
Direct hybrid retrieval → answer. Optimized for voice and real-time chat.

### Accurate Mode
Query rewrite → hybrid retrieval → Gemini reranker → answer. Handles ambiguous queries, figure references, and equation-heavy questions.

---

## Ingestion

### Fast Tier
PyPDFLoader + pdfplumber tables. No LLM calls. Instant.

### Rich Tier
pymupdf4llm + Gemini image captioning + Groq semantic enrichment with equation rewriting. Each chunk gets topic, summary, and clean equation descriptions for better embedding quality.

---

## Chunking

Structure-aware: sections → headers → recursive fallback. Each chunk stores:

```python
{
    "section_title", "topic", "summary",
    "contains_equation", "equation_description",
    "page_start", "page_end"
}
```

Garbled PDF equations like `_Wi[Q] ∈_ R d[model] ×][d][k` are rewritten to `W_i^Q ∈ R^{d_model × d_k}` during enrichment before embedding.

---

## Evaluation

Retrieval metrics on "Attention Is All You Need" (70 questions, 7 categories):

| Mode | MRR | nDCG | Coverage |
|------|-----|------|----------|
| Fast | 0.74 | 0.75 | 87.6% |
| Accurate | 0.83 | 0.84 | 91.4% |

Categories: direct fact, concept, equation, table lookup, reasoning, comparison, multimodal.

---

## Stack

| Component | Model/Library |
|-----------|--------------|
| Embeddings | OpenAI `text-embedding-3-small` |
| Answering | Groq `gpt-oss-120b` |
| Reranking | Gemini 2.5 Flash Lite |
| Enrichment | Groq `llama-3.1-8b-instant` |
| Image captioning | Gemini 2.5 Flash Lite |
| Vector store | ChromaDB Cloud |
| Keyword search | BM25 (`rank-bm25`) |

---

## Setup

```bash
uv sync
```

```env
OPENAI_API_KEY=
GROQ_API_KEY=
GEMINI_API_KEY=
CHROMA_API_KEY=
CHROMA_TENANT=
CHROMA_DATABASE=
```

---

## Usage

```python
# Ingest
processor = SmartPDFProcessor(gemini_api_key=..., groq_api_key=...)
chunks = processor.process_pdf_rich("paper.pdf")

# Query
answer, chunks = answer_question(
    question="What is scaled dot-product attention?",
    mode="accurate",
    bm25_index=bm25_index,
)

# Stream
generator, chunks = stream_answer_with_sources(
    question="Explain multi-head attention",
    mode="fast",
    bm25_index=bm25_index,
)
```

---

## Gradio UI

Upload PDFs and ask questions with a two-panel chat interface showing retrieved sources, section metadata, and relevance scores.

```bash
uv run chat_app.py
```