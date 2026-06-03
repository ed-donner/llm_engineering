# Suggested PR title

**feat(week5): KUCCPS Cluster Calculator & RAG University Advisor for Kenyan KCSE students**

---

# Suggested PR description (for GitHub)

## Summary

Adds a **Week 5 community contribution**: a RAG-based advisor for the **Kenyan education system** that helps students and parents choose courses and institutions after KCSE.

## Problem

After KCSE (Kenya Certificate of Secondary Education), students and parents often struggle to find suitable degree programmes and universities. Cluster points, cut-offs, and programme requirements are hard to navigate. This tool addresses that by computing **cluster points** (the metric KUCCPS uses) and suggesting **up to 4 universities** with expert guidance via RAG.

## What’s included

- **`clusters/`** – Python port of the official KUCCPS cluster formula (no UI): grade points, 6 clusters, weighted cluster **C = √((r/48)×(t/84))×48**.
- **RAG pipeline** – Knowledge base (KUCCPS overview, universities & courses, expert guidance) embedded with **SentenceTransformer** (`all-MiniLM-L6-v2`), stored in **Chroma**; answers via **OpenRouter** LLM.
- **Gradio app** – Enter KCSE grades, select cluster, enter course of interest → see cluster result and recommendations (at most 4 universities + guidance).
- **README** – Explains Kenyan context, problem, setup (ingest then app), and cost notes (local embeddings, economical LLM).

## Tech stack

- Python 3, `python-dotenv`, `chromadb`, `sentence-transformers`, `openai`, `gradio`.
- `.env` loaded from repo root (`OPENROUTER_API_KEY` or `OPENAI_API_KEY`).

## How to run

1. Set `OPENROUTER_API_KEY` (or `OPENAI_API_KEY`) in `.env` at repo root.
2. `cd week5/community-contributions/makinda && python3 ingest.py` (first time or after editing `knowledge_base/`).
3. `python3 app.py` → Gradio opens in browser.

---

# Suggested merge commit message (when merging the PR)

```
feat(week5): KUCCPS Cluster Calculator & RAG advisor for Kenyan KCSE students

- Add RAG-based advisor: cluster points + university recommendations (at most 4)
- Python port of KUCCPS formula in clusters/ (SentenceTransformer + Chroma + OpenRouter)
- Gradio UI: grades, cluster, course interest → cluster result + guidance
- README explains Kenyan context and post-KCSE course/institution selection problem
```
