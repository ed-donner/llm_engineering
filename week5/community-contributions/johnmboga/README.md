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

## 📁 Project Structure

```
legal_rag/
├── app.py              # Main Gradio app (full RAG pipeline)
├── ingest.py           # One-time ingestion script
├── requirements.txt    # Python dependencies
├── .env                # Your OpenAI API key (create this)
├── sample_data/        # Built-in Kenyan legal documents
│   ├── kenya_constitution_2010.txt
│   ├── kenya_contract_law.txt
│   ├── kenya_criminal_law.txt
│   └── kenya_land_law.txt
└── chroma_db/          # Created automatically after ingestion
```

## 🚀 Setup & Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your OpenAI API key

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-your-key-here
```

### 3. Ingest sample documents (run once)

```bash
python ingest.py
```

### 4. Start the app

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

## 💡 Advanced Extensions (as shown in course)

- Connect to Google Drive API to read your own docs automatically
- Add MS Office document support with `python-docx`
- Connect to your Gmail to search legal correspondence
- Add Slack integration for team knowledge sharing
