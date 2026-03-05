## Week 5 – WikiQA RAG Assistant (abdussamadbello)

This Week 5 exercise implements a small **Retrieval-Augmented Generation (RAG) assistant** on top of the `wiki_qa` dataset.

- The assistant uses the `answer` sentences from `wiki_qa` as a mini knowledge base.
- For each user question, it retrieves the most relevant sentences and asks a frontier model to:
  - **Answer** the question concisely
  - **Explain** the answer
  - **Show explicit evidence** (numbered sentences with titles)

All of this is exposed through a simple **Gradio chat UI**: chat on the left, retrieved evidence on the right.

### Files

- `week5-assignment.ipynb`: main notebook with dataset loading, vector store, RAG function, and Gradio app.

### Dependencies

You can install the required packages with:

```bash
pip install datasets openai python-dotenv langchain-core langchain-chroma langchain-huggingface sentence-transformers gradio
```

You also need an OpenAI-compatible API key with access to `gpt-4.1-nano` (or update the model name in the notebook).

### Environment

Create a `.env` file (do **not** commit it) with:

```bash
OPENAI_API_KEY=your_openai_key_here
```

### How to run

1. Ensure dependencies are installed and `.env` is set up.
2. Open `week5-assignment.ipynb` in Jupyter / VS Code / Cursor.
3. Run all cells up to (and including) the Gradio app definition.
4. Uncomment `demo.launch()` in the last cell and run it to start the UI.
5. In the browser tab that opens, ask Wikipedia-style questions and inspect the evidence panel for the retrieved `wiki_qa` sentences.

