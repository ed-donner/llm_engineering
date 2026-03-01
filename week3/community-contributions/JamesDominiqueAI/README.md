ResumeMatch — Semantic Resume ↔ JD Matching
Lightweight local NLP system for semantic resume screening using transformer embeddings + NER-based skill extraction.
Architecture
Embedding Model:
sentence-transformers/all-MiniLM-L6-v2
384-dim sentence embeddings
Chosen for low latency and small footprint (~80MB) vs larger cross-encoders

NER Model:
dslim/bert-base-NER
Used to extract ORG/MISC entities (technologies, tools, frameworks)
Augmented with curated keyword bank to reduce false negatives

Similarity Metric:
Cosine similarity on normalized embeddings

UI:
Gradio (stateless, no database)

Pipeline
Text normalization
Skill extraction (NER + keyword list)

Resume/JD embedding generation
Cosine similarity scoring
Set-based skill gap analysis
Composite ranking (multi-resume mode)

Composite score:
(similarity% + skill_coverage%) / 2

Why This Design?
Local inference → no API cost, no latency dependency
Bi-encoder embeddings → scalable to many resumes (O(n))
Hybrid skill extraction → improves precision over pure NER
Single-file architecture → easy reproducibility

Trade-off:
Bi-encoder similarity is fast but less precise than cross-encoder reranking.

Features
Single resume vs JD scoring
Skill match / missing / bonus breakdown
Multi-resume ranking
Custom JD presets (session-scoped)

Limitations
No fine-tuning (generic embeddings)
English-only
No PDF parsing (text input only)
Keyword bank may require domain tuning
No persistence layer

Installation
pip install -r requirements.txt
python resume_matcher.py

First run downloads models from HuggingFace.

Extension Points
Cross-encoder reranking for higher precision
Skill ontology mapping (e.g., AWS ↔ Amazon Web Services)
Feedback loop for supervised calibration
Persistent JD storage (SQLite)
Dockerized deployment

Dependencies
Core stack:
torch
sentence-transformers
transformers
scikit-learn
gradio