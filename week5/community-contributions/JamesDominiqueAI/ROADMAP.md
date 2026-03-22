# 📅 Implementation Roadmap — Regulatory Compliance RAG

> **Total duration:** 6 weeks | **Difficulty:** 7/10 | **Interview value:** Very High

---

## Overview

| Week | Phase | Deliverable | Status |
|---|---|---|---|
| 1 | Foundation | Working ingestion pipeline + basic retrieval | ✅ Included |
| 2 | Metadata Intelligence | Filtered retrieval + structured chunks | ✅ Included |
| 3 | Adaptive Core | Self-tuning retrieval loop + confidence scoring | ✅ Included |
| 4 | Answer Generation | Query rewrite + LLM answer + source citation | ✅ Included |
| 5 | Evaluation | MRR/Hit@5 eval suite + comparison reports | ✅ Included |
| 6 | Polish | UI, deployment, stretch goals | 🔜 Next |

---

## Week 1 — Foundation

**Goal:** Get documents chunked, embedded, and retrievable.

### Tasks

- [ ] Set up project structure (`ingest/`, `retrieval/`, `rag/`, `evaluation/`)
- [ ] Build `chunker.py` — load `.md` files, split into `Chunk` objects
- [ ] Define `Chunk` data model with metadata fields (`regulation_id`, `year`, `section`)
- [ ] Build `embedder.py` — embed chunks using `sentence-transformers`
- [ ] Set up ChromaDB persistent collection
- [ ] Build `base_retrieval.py` — cosine similarity query
- [ ] Write `config.py` with all tunable parameters
- [ ] Manual test: ask 3 questions, inspect returned chunks

### Success Criteria
- Index builds without errors
- Top-3 retrieved chunks for a test question are visually relevant

### Commands
```bash
pip install -r requirements.txt
python app.py --ingest
python app.py --query "What are the breach notification requirements?"
```

---

## Week 2 — Metadata Intelligence

**Goal:** Make retrieval regulation-aware, not just semantically close.

### Tasks

- [ ] Build `metadata_filters.py` — extract year, regulation ID, doc type from question
- [ ] Integrate metadata filters into `base_retrieval.py` (ChromaDB `where` clause)
- [ ] Test: "What does REG-ABC-2021 say?" vs "What does REG-ABC-2023 say?" → different results
- [ ] Add fallback: if filtered query returns 0 results, retry without filter
- [ ] Add `doc_type` filtering for amendment/guidance/audit queries
- [ ] Log which filters were applied per query

### Success Criteria
- Year filter correctly restricts results to matching year
- "What changed in 2023?" returns 2023 documents first
- Filter failure gracefully falls back to unfiltered retrieval

### Test Questions
```
"What are the breach rules in 2021?"         → should hit reg_abc_2021
"What are the breach rules in 2023?"         → should hit reg_abc_2023
"What did the 2022 audit find?"              → should hit audit_2022_annual
"What did the 2022 amendment say?"           → should hit amd_abc_2022_a1
```

---

## Week 3 — Adaptive Self-Tuning Retrieval

**Goal:** The system should automatically improve retrieval quality without user involvement.

### Tasks

- [ ] Build `adaptive_controller.py` — retry loop with k-widening
- [ ] Implement `compute_keyword_overlap()` — question keywords vs chunk text
- [ ] Implement `average_embedding_similarity()` — mean cosine score of top-5
- [ ] Implement `retrieval_confidence_score()` — 60/40 weighted composite
- [ ] Implement `rewrite_query()` — 3-level progressive expansion
- [ ] Add trace logging (attempts, rewrites, scores per attempt)
- [ ] Test: vague question "What changed?" should trigger rewrite

### Success Criteria
- Low-quality first attempt (score < 0.4) triggers query rewrite
- At least 1 of 3 test vague questions improves score by ≥ 0.15 after adaptation
- Trace dict shows full decision log

### Key Metrics to Track
```
Attempt 1 confidence: 0.42
  → Score < MIN_CONFIDENCE_FOR_REWRITE (0.40): rewrite triggered
  → New query: "amendments introduced in 2023 compared to 2022..."
Attempt 2 confidence: 0.79 ✅
  → Above CONFIDENCE_THRESHOLD (0.75): accepted
```

---

## Week 4 — Answer Generation

**Goal:** Transform retrieved chunks into a clear, cited, confidence-labelled answer.

### Tasks

- [ ] Build `rag/rewrite.py` — `detect_intent()` with 6 categories
- [ ] Build `rag/answer.py` — OpenAI call with system prompt + context
- [ ] Add mock fallback answer (template-based) for offline use
- [ ] Build `_build_context()` — format chunks with reg ID + year labels
- [ ] Add confidence labelling: HIGH / MEDIUM / LOW with color mapping
- [ ] Add structured source citations in output
- [ ] Wire together in `app.py`: question → intent → rewrite → adaptive → answer
- [ ] Test full pipeline end-to-end

### Success Criteria
- Answer cites specific regulation IDs and sections
- Confidence label reflects actual retrieval quality
- Mock mode works without any API key

### Sample Output
```
ANSWER:
According to REG-ABC-2021 (Section 4), institutions must notify the FFCA
within 72 hours of discovering a breach. This was tightened in REG-ABC-2023
to 48 hours...

CONFIDENCE: 0.83 (HIGH ✅)
SOURCES:
  • REG-ABC-2023 (2023) — Section 4  [relevance: 0.91]
  • REG-ABC-2021 (2021) — Section 4  [relevance: 0.87]
```

---

## Week 5 — Evaluation Suite

**Goal:** Prove the system works and quantify the adaptive improvement.

### Tasks

- [ ] Build `evaluation/retrieval_eval.py` with 10 labelled test questions
- [ ] Implement MRR (Mean Reciprocal Rank) scoring
- [ ] Implement Hit@5 (did any expected reg appear in top 5?)
- [ ] Implement keyword hit rate (did expected terms appear in chunks?)
- [ ] Run basic vs. adaptive comparison and save JSON report
- [ ] Build `evaluation/answer_eval.py` for end-to-end quality
- [ ] Add question categories: `direct_fact`, `temporal_change`, `cross_reference`, `penalty_lookup`
- [ ] Document results in this roadmap

### Success Criteria
- Adaptive retrieval shows ≥ 10% MRR improvement over basic
- Evaluation runs automatically without manual inspection
- Results saved to `eval_results/` as JSON

### Target Results
```
BASIC:     MRR=0.61  Hit@5=0.70  Confidence=0.58
ADAPTIVE:  MRR=0.84  Hit@5=0.90  Confidence=0.79
                  ↑ +0.23       ↑ +0.21
```

---

## Week 6 — Polish, UI & Deployment

**Goal:** Make it demo-ready and deployment-ready.

### Tasks

#### Option A: Streamlit UI (Recommended)
```bash
pip install streamlit
streamlit run streamlit_app.py
```

Features to build:
- [ ] Chat-style input with answer display
- [ ] Confidence badge (🟢 HIGH / 🟡 MEDIUM / 🔴 LOW)
- [ ] Source cards showing regulation ID, year, section
- [ ] Adaptive trace expander (show attempts + rewrites)
- [ ] Filter sidebar (year range, doc type)
- [ ] Evaluation dashboard tab

#### Option B: FastAPI REST API
```python
POST /query
  body: {"question": "..."}
  returns: {"answer": "...", "confidence": 0.83, "sources": [...]}

GET /stats
GET /eval
```

#### Option C: Both (Full Stack)
- FastAPI backend
- Simple HTML/JS frontend

### Stretch Goals
- [ ] Add a `FeedbackStore` — let users rate answers (👍/👎), save to SQLite
- [ ] Implement re-ranking using a cross-encoder model
- [ ] Add conversation memory (multi-turn Q&A)
- [ ] Support PDF ingestion (not just markdown)
- [ ] Docker deployment with `docker-compose.yml`

---

## 🏆 What This Project Demonstrates

When presenting this in interviews or on GitHub:

1. **RAG internals** — You understand chunking, embedding, vector retrieval, and prompting
2. **Retrieval quality metrics** — You measure MRR and hit-rate, not just "it works"
3. **Feedback loops** — The system improves itself without retraining
4. **Clean architecture** — Each module has a single responsibility
5. **Cloud architect thinking** — Metadata filtering, fallback logic, separation of concerns
6. **Domain knowledge** — You applied it to a realistic regulated industry context

---

## 📌 Quick Reference: File Creation Order

If starting from scratch:

```
Week 1:  config.py → chunker.py → embedder.py → base_retrieval.py → app.py (basic)
Week 2:  metadata_filters.py → update base_retrieval.py
Week 3:  adaptive_controller.py
Week 4:  rewrite.py → answer.py → update app.py (full pipeline)
Week 5:  retrieval_eval.py → answer_eval.py
Week 6:  streamlit_app.py or api.py
```
