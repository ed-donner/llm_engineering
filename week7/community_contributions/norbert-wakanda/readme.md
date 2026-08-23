# Jumia AI Product Advisor

An agentic AI shopping assistant for Jumia, Africa's leading e-commerce platform. The agent combines a fine-tuned Llama pricing model, a RAG knowledge base, and live web search to help users evaluate product prices and find deals.

## How It Works

The agent (powered by Claude Haiku) orchestrates four tools in a reasoning loop:

1. **`llama_price_estimate`** — Runs a fine-tuned Llama 3.2-3B model (loaded in 4-bit NF4 quantization) to estimate a product's fair market price from its description.
2. **`rag_search`** — Queries a local ChromaDB vector store built from Jumia markdown documents (products, policies, services). Chunks are generated and reranked by Claude for relevance.
3. **`web_search`** — Uses DuckDuckGo to find real-time listings and prices on Jumia or other African e-commerce platforms.
4. **`compare_prices`** — Compares the Llama estimate against a real listing price and returns a deal verdict (great deal → overpriced).

A Gradio UI wraps the agent with a chat interface and a one-click knowledge base initializer.

## Stack

| Component | Technology |
|---|---|
| Orchestration LLM | `claude-haiku-4-5` (Anthropic) |
| Pricing model | Fine-tuned `meta-llama/Llama-3.2-3B` via PEFT/LoRA |
| Vector store | ChromaDB (persistent) |
| Embeddings | `all-MiniLM-L6-v2` (HuggingFace) |
| Web search | DuckDuckGo (`langchain-community`) |
| UI | Gradio |
| Runtime | Google Colab (GPU) |

## Setup (Google Colab)

This project is designed to run on **Google Colab** to take advantage of a free CUDA GPU for the Llama pricing model.

**1. Open the notebook in Colab:**

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1d2OqUJPzqZT3LILuWip8xdb0TKEf0roY#scrollTo=aql4NXtCmVWe)

**2. Download the knowledge base:**

The Jumia knowledge base (markdown files covering products, pricing, company info, employees, and contracts) is hosted on Google Drive:

📁 [Download knowledge-base](https://drive.google.com/drive/folders/1Yq8lk0Utykj8gQ1lkqqWkvkw9GfOEgja?usp=sharing)

Mount your Google Drive in Colab or upload the `knowledge-base/` folder directly to your Colab session so it sits alongside the notebook:

```
knowledge-base/
├── company/
├── contracts/
├── employees/
├── pricing/
└── products/
```

**3. Set your API keys** in a `.env` file or as Colab secrets:

```
ANTHROPIC_API_KEY=your_key
HF_TOKEN=your_huggingface_token
```

**4. Install dependencies:**

```bash
pip install torch transformers peft bitsandbytes gradio chromadb \
            langchain langchain-anthropic langchain-huggingface \
            langchain-community pydantic tqdm python-dotenv
```

## Running

Run all cells in the notebook. The Gradio app will launch with a public share link. Click **Initialize / Refresh Knowledge Base** on first run to chunk, embed, and index the knowledge base into ChromaDB.

**Example prompts:**
- *Is a Samsung Galaxy S24 for $400 a good deal?*
- *What are Jumia Express delivery fees?*
- *How does JumiaPay work?*
