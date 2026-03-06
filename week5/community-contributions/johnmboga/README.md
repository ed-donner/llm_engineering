# ⚖️ KenyaLex — AI Legal Assistant for Law Students

A full RAG (Retrieval-Augmented Generation) demo app built for a Udemy LLM Engineering class exercise. Specialised in Kenyan law.

## 🧠 RAG Pipeline Architecture

```
INGESTION:
  Files (PDF/TXT)
    → Load (LangChain DirectoryLoader)
    → Chunk (RecursiveCharacterTextSplitter, 800 tokens, 150 overlap)
    → Encode (OpenAI text-embedding-3-small)
    → Store (ChromaDB vector database)

QUERY:
  User Question
    → [LLM] Enrich question with legal terminology (HyDE-style)
    → [ChromaDB] Retrieve top-K chunks (dual query: original + enriched)
    → [LLM] Rerank chunks by relevance, keep top-N
    → [LLM] Generate answer using chunks as system context
    → Display answer with sources
```

## 🚀 Setup & Run

### 1. Ingest sample documents (run once)

```bash
python ingest.py
```

### 2. Start the app

```bash
python app.py
```

Then open: http://localhost:7860

## 📚 Built-In Knowledge Base

| Document                   | Coverage                                                   |
| -------------------------- | ---------------------------------------------------------- |
| Constitution of Kenya 2010 | Bill of Rights (Arts 19–40), Executive, Judiciary          |
| Contract Law               | Elements, breach, remedies, 6 eKLR cases                   |
| Criminal Law (Penal Code)  | Murder, manslaughter, robbery, sexual offences, cybercrime |
| Land Law                   | Land Act 2012, adverse possession, matrimonial property    |

## 🔑 Key Features

- **Ask questions** about Kenyan law with cited answers
- **Upload your own PDFs/TXTs** (lecture notes, case files, statutes)
- **RAG pipeline trace** — see enriched query, retrieved chunks, rerank scores
- **Example questions** to demo to class
