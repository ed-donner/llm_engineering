# KUCCPS Cluster Calculator & University Advisor (RAG)

**Context for instructors and students:** This project applies to the **Kenyan education system**. After secondary school, students sit the **KCSE** (Kenya Certificate of Secondary Education). Placement into degree programmes at universities and colleges is managed by **KUCCPS** (Kenya Universities and Colleges Central Placement Service). Many **students and parents struggle to identify suitable courses and institutions**—cut-off points, cluster requirements, and programme options are hard to navigate. This tool helps by computing a student’s **cluster points** (the metric KUCCPS uses) and by using **RAG** to suggest **at most 4 universities** and practical guidance based on their grades and course interest.

Week 5 community contribution: a **RAG-based advisor** that lets users enter KCSE grades and a course of interest, then shows **cluster points** (using the official KUCCPS formula) and recommends **at most 4 universities** with expert guidance.

## Problem

After KCSE, students and parents often find it difficult to choose the right courses and institutions. Cluster points, cut-offs, and programme requirements are not always easy to interpret. This app addresses that by (1) calculating cluster points transparently and (2) using a RAG knowledge base to suggest universities and guidance tailored to the student’s profile.

## Features

- **Cluster points**: Python port of the KUCCPS cluster formula from the reference TypeScript calculator (no UI in the formula; logic lives in `clusters/`).
- **RAG**: Knowledge base (KUCCPS overview, universities & courses, expert guidance) is embedded with **SentenceTransformer** (`all-MiniLM-L6-v2`) and stored in **Chroma**. Queries are answered with retrieved context + **OpenRouter** LLM for cost-effective runs.
- **Gradio UI**: Input grades per subject, select cluster, enter course of interest → see weighted cluster, raw cluster, aggregate, and a short recommendation (up to 4 universities + guidance).

## Data files / PDFs

**Per repo guidelines:** Data files and PDFs are not checked into this repo. The **cluster-related PDFs** (e.g. official KUCCPS cluster/subject documents) that were previously in the `clusters/` folder are hosted in a central location for download:

- **Cluster PDFs (KUCCPS):** [Download from Google Drive](https://drive.google.com/drive/folders/1s8ukjzQOsVUJMsRCcsVtAwA77z3At8Lg?usp=sharing)

After downloading, you can keep the PDFs locally (e.g. in `clusters/` or a `data/` folder) for reference. The RAG pipeline currently ingests only the markdown files in `knowledge_base/`; the repo does not commit any PDFs or large data files.

## Setup

1. **Environment**  
   `.env` is loaded from the **project root** (`llm_engineering/`). Ensure you have:
   - `OPENROUTER_API_KEY` (or `OPENAI_API_KEY`) for the LLM.

2. **Install dependencies** (from repo root or this folder):

   ```bash
   pip install -r week5/community-contributions/makinda/requirements.txt
   ```

   Or use the main repo `requirements.txt` (already includes `chromadb`, `sentence_transformers`, `gradio`, `python-dotenv`, `openai`).

3. **Build the vector store** (first time, or after changing `knowledge_base/`):

   ```bash
   cd week5/community-contributions/makinda && python ingest.py
   ```

   This reads `knowledge_base/*.md`, chunks them, embeds with SentenceTransformer, and writes to `vector_db/`.

4. **Run the app**:
   ```bash
   cd week5/community-contributions/makinda && python app.py
   ```
   Or from repo root: `python week5/community-contributions/makinda/app.py`  
   Gradio will open in the browser.

## Layout

- `clusters/` – Cluster constants and calculator (formula: C = √((r/48)×(t/84))×48; aggregate = best 7, raw cluster = best 4 cluster subjects).
- `knowledge_base/` – Markdown docs for RAG (KUCCPS overview, universities & courses, expert guidance).
- `ingest.py` – Builds Chroma index from `knowledge_base/` using SentenceTransformer.
- `answer.py` – Retrieves from Chroma, calls OpenRouter LLM, returns guidance (at most 4 universities).
- `app.py` – Gradio UI: grades, cluster, course of interest → cluster result + RAG recommendations.

## Cost notes

- Embeddings: local `all-MiniLM-L6-v2` (no API cost).
- LLM: OpenRouter with a small model (e.g. `openai/gpt-4o-mini`) to keep the exercise economical.
