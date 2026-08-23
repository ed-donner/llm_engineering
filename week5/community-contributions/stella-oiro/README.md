# Clinical Guidelines RAG Assistant — Week 5

A RAG-powered chatbot that answers clinical questions from a structured medical knowledge base.

## What it does

- Loads 12 reference documents across three categories: clinical guidelines (hypertension, T2DM, asthma, heart failure, sepsis), drug references (antibiotics, antihypertensives, insulin), and scoring tools (Wells, CURB-65, CHA2DS2-VASc, GCS)
- Pipeline: LangChain DirectoryLoader → RecursiveCharacterTextSplitter → HuggingFace `all-MiniLM-L6-v2` embeddings → ChromaDB → GPT-4.1-mini → Gradio ChatInterface

## Setup

### 1. Download the knowledge base

Download the `clinical-knowledge-base/` folder from Google Drive and place it in this directory:

> **[Download clinical-knowledge-base from Google Drive](https://drive.google.com/drive/folders/1oF_23opeXH5f-rWQDig0otg5jMZRBkSc?usp=sharing)**

The folder structure should look like:
```
clinical-knowledge-base/
  guidelines/
    hypertension.md
    type2-diabetes.md
    asthma.md
    heart-failure.md
    sepsis.md
  drugs/
    common-antibiotics.md
    antihypertensives.md
    insulin-types.md
  scoring-tools/
    wells-score.md
    curb65.md
    chadsvasc.md
    glasgow-coma.md
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Set up your `.env` file

```
OPENAI_API_KEY=sk-...
```

### 4. Run the notebook

Open `clinical_rag_assistant.ipynb` and run all cells.
