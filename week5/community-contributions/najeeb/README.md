# Private Knowledge Worker – Exercise

A small RAG-based chat that answers from **your own** documents. Combines **Week 5** (RAG pipeline) and **Week 2** (Gradio + tooling).

## What it does

- Loads markdown (`.md`) files from a folder you choose.
- Chunks them, embeds with **HuggingFace** `all-MiniLM-L6-v2` (no API key).
- Stores vectors in **Chroma** on disk.
- **Tooling:** The LLM has a `search_knowledge(query)` tool and decides when to search; the app handles `tool_calls` and feeds results back (see step 6 in the notebook).
- **Gradio** chat UI to talk to the assistant.

## How to run

1. Open `private_knowledge_worker.ipynb` in this folder (`week5/private_knowledge_worker/`).
2. Run the notebook (from repo root or from `week5/private_knowledge_worker/`). The notebook resolves `KNOWLEDGE_BASE_PATH` to week5’s knowledge base automatically. For OpenAI, put `.env` in the repo root and start Jupyter from there so `load_dotenv()` finds it. Or set it to your own folder for a “private” knowledge base.
3. Run cells 1–4 to load docs, build the vector store, and set up the retriever + LLM.
4. Run the last cell to launch the Gradio app; chat in the browser.

## LLM choice

- **OpenAI:** Set `OPENAI_API_KEY` in `.env` (in the project root). The notebook uses `gpt-4.1-nano` (or switch to `gpt-4.1-mini`).
- **Fully local:** Don’t set `OPENAI_API_KEY`, or set `USE_OLLAMA = True`. Run [Ollama](https://ollama.ai) and pull a model (e.g. `llama3.2`). The notebook will use `http://localhost:11434/v1`.

## Download pre-built vector store (optional)

The Chroma vector store is not stored in the repo. To use a pre-built index instead of building it from the knowledge base, download and extract it here:

- **[private_kb_chroma.zip (Google Drive)](https://drive.google.com/file/d/1vi87k5DtBIh8KliRxWPw9J9PtAKk-9mS/view?usp=sharing)**

Extract the zip in this folder so that `private_kb_chroma/` sits next to `private_knowledge_worker.ipynb`. Otherwise, run the "Build the vector store" cell in the notebook to create it from the knowledge base.

## How the tool loop works (step 6)

The notebook implements **search as a tool**: the LLM can call `search_knowledge(query)`. When the API returns `finish_reason == "tool_calls"`, we run the retriever with the model’s query, append the tool results to the conversation, and call the API again until the model returns a normal text response. See **week2/day4.ipynb** for the same pattern with multiple tools.
