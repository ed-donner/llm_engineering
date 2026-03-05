# 🏛️ Regulatory Compliance RAG

> **Adaptive Self-Tuning Retrieval-Augmented Generation for Financial Regulatory Documents**

A production-quality RAG system that retrieves and answers questions about financial regulations — with adaptive retrieval that improves its own search quality in real time.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **Adaptive Retrieval Loop** | Automatically widens search scope and rewrites queries if initial confidence is low |
| **Intent Detection** | Classifies questions as temporal changes, penalty lookups, cross-references, etc. |
| **Metadata-Aware Filtering** | Filters by year, regulation ID, and document type before embedding search |
| **Confidence Scoring** | Hybrid heuristic: 60% keyword overlap + 40% semantic similarity |
| **No ML Training Required** | All intelligence is heuristic-based — runs fully locally |
| **OpenAI Optional** | Works offline with template answers; plug in OpenAI key for full LLM answers |
| **Built-in Evaluation Suite** | MRR, Hit@5, keyword hit rate — compare basic vs. adaptive retrieval |

---

## 🏗️ Architecture

```
User Question
    ↓
Intent Detection (temporal? penalty? cross-reference?)
    ↓
Query Rewrite (improves retrieval specificity)
    ↓
Adaptive Retrieval Loop
  → Attempt 1: k=10, score chunks
  → If confidence < 0.75: widen k, rewrite query, retry
  → Max 3 attempts
    ↓
Rerank by cosine similarity
    ↓
Answer Generation (OpenAI GPT-4o-mini or template fallback)
    ↓
Confidence Score + Source Citations
```

---

## 📁 Project Structure

```
regulatory_rag/
│
├── knowledge-base/               # 📚 Your regulatory documents (.md files)
│   ├── regulations/
│   │   ├── reg_abc_2021.md
│   │   ├── reg_abc_2023.md
│   │   └── reg_xyz_2022.md
│   ├── amendments/
│   │   └── amd_abc_2022_a1.md
│   ├── guidance/
│   │   └── gn_2023_04_cloud.md
│   └── audit_reports/
│       └── audit_2022_annual.md
│
├── ingest/
│   ├── chunker.py                # Load & split docs into Chunk objects
│   └── embedder.py               # Embed chunks → ChromaDB
│
├── retrieval/
│   ├── base_retrieval.py         # Core vector search
│   ├── adaptive_controller.py    # Adaptive loop + confidence scoring
│   └── metadata_filters.py       # Extract year/regulation filters from question
│
├── rag/
│   ├── rewrite.py                # Intent detection + query rewriting
│   └── answer.py                 # Answer generation (OpenAI / mock fallback)
│
├── evaluation/
│   ├── retrieval_eval.py         # MRR, Hit@5 evaluation suite
│   └── answer_eval.py            # End-to-end answer quality eval
│
├── app.py                        # 🚀 Main CLI entry point
├── config.py                     # Central configuration
└── requirements.txt
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> **Runs fully locally.** No API key needed for embeddings — uses `sentence-transformers` (all-MiniLM-L6-v2).
> For full LLM-generated answers, optionally set: `export OPENAI_API_KEY="sk-..."`

### 2. Build the index

```bash
python app.py --ingest
```

Processes all `.md` files in `knowledge-base/`, generates embeddings, and stores them in ChromaDB.

### 3. Ask a question

```bash
python app.py --query "What changed in breach notification requirements in 2023?"
python app.py --query "What is the penalty for unauthorized data sharing?"
python app.py --query "What are the KYC requirements under REG-XYZ-2022?"
```

### 4. Interactive mode

```bash
python app.py
```

### 5. Run evaluation

```bash
python app.py --eval           # Retrieval quality (MRR, Hit@5)
python app.py --eval-answers   # Full pipeline quality
```

---

## 🧠 Adaptive Retrieval — How It Works

The system automatically improves retrieval quality without any ML training:

```
Attempt 1: k=10 chunks
  → Confidence score = 0.52  (below threshold 0.75)
  → Score < 0.40? → Rewrite query
  → Increase k to 20

Attempt 2: k=20 chunks, rewritten query
  → Confidence score = 0.81  ✅ threshold met
  → Accept result
```

**Confidence formula:**
```
confidence = 0.6 × keyword_overlap + 0.4 × avg_semantic_similarity
```

---

## 📊 Confidence Score Display

| Score | Label | Meaning |
|---|---|---|
| ≥ 0.75 | 🟢 HIGH | Strong retrieval, reliable answer |
| 0.50–0.74 | 🟡 MEDIUM | Moderate confidence, verify sources |
| < 0.50 | 🔴 LOW | Weak retrieval, consider rephrasing |

---

## 📦 Adding Your Own Documents

Add `.md` files to `knowledge-base/` in any subfolder:

```markdown
# Your Regulation Title

**Regulation ID:** REG-XYZ-2024
**Year:** 2024

## Section 1: ...
```

Then rebuild the index:

```bash
python app.py --force-reingest
```

The system auto-extracts regulation ID, year, and document type from content and file path.

---

## ⚙️ Configuration

Edit `config.py` to tune the system:

```python
DEFAULT_K = 10               # Starting number of chunks
CONFIDENCE_THRESHOLD = 0.75  # Accept retrieval above this
MIN_CONFIDENCE_FOR_REWRITE = 0.4  # Rewrite query below this
ADAPTIVE_MAX_ATTEMPTS = 3    # Max retries
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Local embedding model
```

---

## 🧪 Evaluation Results (Sample)

```
BASIC RETRIEVAL:     MRR=0.61   Hit@5=0.70   Confidence=0.58
ADAPTIVE RETRIEVAL:  MRR=0.84   Hit@5=0.90   Confidence=0.79
                              ↑ +0.23        ↑ +0.21
```

---

## 🔧 Tech Stack

| Layer | Technology |
|---|---|
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2) |
| Vector Store | `ChromaDB` (persistent, local) |
| LLM | OpenAI GPT-4o-mini (optional) |
| Language | Python 3.9+ |
| Data Model | Python dataclasses + Pydantic |

---

## 📋 License

MIT License — free to use and extend.
