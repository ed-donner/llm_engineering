# Week 5 Exercise – SafeHire AI Risk Advisor (winniekariuki)

**SafeHire AI Risk Advisor** — A decision-support tool for parents. Evaluates hiring risk of domestic workers using a knowledge base and nanny profiles. Helps answer: *"Is this nanny safe to hire?"*

## What's included

- **Knowledge base**: `knowledge-base/safehire_knowledge.md` — consolidated guidelines on compliance, red flags, hiring best practices, reference verification, trust scores, child safety.
- **Nanny profiles**: `profiles/nanny_profiles.json` — structured profiles; when you ask about a nanny by name, their profile is injected into the prompt.
- **RAG pipeline**: Load → chunk (RecursiveCharacterTextSplitter 500/50) → embed (OpenAI) → Chroma → retrieve (top‑3) → generate (gpt-4o-mini).
- **Gradio UI**: Simple chat — question input, response output.

## How to run

1. From `week5/community-contributions/winniekariuki/`, install: `langchain-community`, `langchain-text-splitters`, `langchain-openai`, `langchain-chroma`, `chromadb`, `gradio`, `python-dotenv`.
2. Set `OPENAI_API_KEY` in `.env`.
3. Open `week5_exercise.ipynb` and run all cells. The Gradio app will launch.
