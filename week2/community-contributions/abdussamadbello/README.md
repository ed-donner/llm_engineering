## Week 2 – LLM Engineering Translator (abdussamadbello)

This folder contains my solution for the Week 2 exercise: a small **LLM Engineering-aware translator** for technical content about prompts, tools/agents, retrieval, and evaluation.

The notebook `week2-assignment.ipynb`:
- Translates LLM-engineering text between **English and French**
- Uses OpenAI `gpt-4o-mini` with a focused system prompt that preserves code blocks and technical terms
- Demonstrates the translation on a prompt-design block for a retrieval-augmented generation (RAG) assistant

### How to run

1. Ensure you have an `.env` with a valid `OPENAI_API_KEY` in your environment (not committed to the repo).
2. Open `week2-assignment.ipynb` in Jupyter / VS Code / Cursor.
3. Run all cells to:
   - Initialize the OpenAI client
   - Translate the example LLM-engineering prompt-design text from **English → French**
4. Optionally, modify `example_text` or the `direction` argument to explore other LLM-engineering snippets or translate **French → English**.

