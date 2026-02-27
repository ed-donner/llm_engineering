## Week 1 – LLM Engineering Tutor (abdussamadbello)

This folder contains my solution for the Week 1 exercise: a small **LLM Engineering technical tutor** that helps developers design, debug, and deploy LLM‑powered applications.

The notebook `week1-assignment.ipynb`:
- Takes an LLM‑engineering question (about prompt design, tools/agents, retrieval, or evaluation)
- Sends it to both a **frontier model** (OpenAI `gpt-4o-mini`) and a **local model** (Ollama `llama3.2`)
- Returns clear, practical explanations from both models so you can compare their answers

### How to run

1. Ensure you have an `.env` with a valid `OPENAI_API_KEY` in your environment (not committed to the repo).
2. Start Ollama and pull the model:
   - `ollama run llama3.2`
3. Open `week1-assignment.ipynb` in Jupyter / VS Code / Cursor.
4. Run all cells to:
   - Initialize the OpenAI and Ollama clients
   - Send the example LLM‑engineering question about **RAG prompt design**
   - View and compare responses from both models.

You can modify the question in the last cell to explore other LLM‑engineering topics such as tools, agents, retrieval, and evaluation.

