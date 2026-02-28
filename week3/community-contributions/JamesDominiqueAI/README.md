# ◈ ResumeMatch — AI-Powered Resume · Job Description Matching System

> Semantic resume screening powered by HuggingFace Transformers and Gradio.  
> Instantly score, match, and rank resumes against any job description.

---

## 📸 Overview

ResumeMatch is a local NLP application that compares a resume against a job description using **semantic embeddings** and **named entity recognition**. It extracts skills automatically, computes a similarity score, highlights what's missing, and can rank multiple candidates against a single role — all through a polished Gradio web UI.

---

## 🧠 Models Used

| Model | Source | Role |
|-------|--------|------|
| `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace | Encodes resume and JD text into 384-dimensional semantic vectors for cosine similarity scoring |
| `dslim/bert-base-NER` | HuggingFace | BERT fine-tuned for NER — used to extract `ORG` / `MISC` entities (technologies, tools, frameworks) from free-form text |

Both models are downloaded automatically from HuggingFace Hub on first run and cached locally.

---

## 🗂 Project Structure

```
resumematch/
├── resume_matcher.py   ← main application (single file)
├── requirements.txt    ← Python dependencies
└── README.md           ← this file
```

---

## 🚀 Quick Start

### 1. Clone / download the repo

```bash
git clone https://github.com/yourname/resumematch.git
cd resumematch
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ **First run** will download ~100 MB of model weights from HuggingFace Hub.  
> Subsequent runs are instant (weights are cached in `~/.cache/huggingface`).

### 4. Run the app

```bash
python resume_matcher.py
```

Open **http://localhost:7860** in your browser.

To generate a public shareable URL (Gradio tunnel), change the last line to:

```python
app.launch(share=True)
```

---

## ✨ Features

### 🎯 Single Resume Analysis
- Select one of **5 built-in job description presets** (ML Engineer, Full Stack Dev, DevOps, Data Engineer, Frontend Dev) or type/paste your own
- Upload resume text and instantly receive:
  - **Semantic similarity score** (0–100 %)
  - **Matched skills** — skills present in both resume and JD
  - **Missing skills** — gaps to close before applying
  - **Bonus skills** — extra resume skills not required by the JD
  - **Skill coverage %** — percentage of JD requirements found in the resume

### 🏆 Rank Multiple Resumes
- Paste any number of resumes separated by `=== RESUME ===`
- Get a ranked leaderboard with 🥇 🥈 🥉 medals
- Composite ranking by `(similarity + skill coverage) / 2`
- Per-candidate skill gap breakdown

### 📌 Custom JD Manager
- Type any job description, give it a name, and save it as a new preset
- Custom presets persist for the duration of the session and appear in all dropdowns

### 📚 JD Library Tab
- Browse and preview all 5 built-in job descriptions in expandable panels

---

## 🏗 Pipeline Architecture

```
Raw Text
   │
   ▼
Step 1 — Clean Text
   Normalize whitespace, strip special characters
   │
   ▼
Step 2 — Extract Skills (NER + keyword bank)
   dslim/bert-base-NER  →  ORG / MISC entities
   Regex scan            →  100+ curated tech skills
   │
   ▼
Step 3 — Create Embeddings
   all-MiniLM-L6-v2  →  384-dim vectors for resume & JD
   │
   ▼
Step 4 — Compute Cosine Similarity
   similarity = cosine(resume_vec, jd_vec)   →  0.0 … 1.0
   │
   ▼
Step 5 — Skill Gap Analysis
   matched  = resume_skills ∩ jd_skills
   missing  = jd_skills − resume_skills
   bonus    = resume_skills − jd_skills
   coverage = |matched| / |jd_skills| × 100
   │
   ▼
Step 6 — Ranking (multi-resume)
   composite = (similarity% + coverage%) / 2
   sort descending → assign medals
```

---

## 📊 Score Interpretation

| Score    | Verdict                        |
|----------|--------------------------------|
| 80–100 % | 🔥 Excellent — strong match    |
| 60–79 %  | ✅ Good — worth interviewing   |
| 40–59 %  | ⚠️ Average — notable skill gaps |
| 0–39 %   | ❌ Poor — major misalignment   |

---

## 💼 Built-in Job Description Presets

| # | Role | Key Required Skills |
|---|------|---------------------|
| 1 | 🤖 Senior ML Engineer | Python, PyTorch, scikit-learn, FastAPI, Docker, Kubernetes, AWS, MLflow |
| 2 | 🌐 Full Stack Web Developer | JavaScript, TypeScript, React, Node.js, PostgreSQL, MongoDB, Docker |
| 3 | ☁️ DevOps / Cloud Engineer | Docker, Kubernetes, Terraform, AWS, GitHub Actions, Prometheus, Grafana |
| 4 | 🗄️ Data Engineer | Python, SQL, Spark, Airflow, dbt, Snowflake, Kafka, BigQuery |
| 5 | 🎨 Frontend Developer (React) | JavaScript, TypeScript, React, Tailwind, Sass, Figma, Jest, Webpack |

---

## ⚙️ Configuration

All configuration lives at the top of `resume_matcher.py`:

| Variable | Description |
|----------|-------------|
| `EMBED_MODEL` | Change to any `sentence-transformers` model name |
| `NER_PIPE` | Swap to any HuggingFace NER model |
| `TECH_SKILLS` | Extend the keyword bank with domain-specific skills |
| `PRESET_JDS` | Add more built-in job descriptions |
| `server_port` | Default `7860` — change to any open port |

---

## 🔧 Troubleshooting

**Models fail to download**  
Check your internet connection. If behind a proxy, set `HTTPS_PROXY` in your environment.

**CUDA / GPU acceleration**  
Install `torch` with CUDA support:  
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

**`aggregation_strategy` error on older Transformers**  
Upgrade to `transformers>=4.20.0`:  
```bash
pip install --upgrade transformers
```

**Port already in use**  
Change `server_port=7860` in the `app.launch()` call at the bottom of the file.

---

## 🛣 Roadmap / Advanced Extensions

- [ ] Cross-encoder reranking (`cross-encoder/ms-marco-MiniLM-L-6-v2`) for higher precision
- [ ] PDF resume upload via `pdfplumber`
- [ ] Export ranking results as CSV
- [ ] Persistent custom JD storage (JSON / SQLite)
- [ ] Explanation generator — LLM-powered hiring recommendation
- [ ] HuggingFace Spaces deployment with `Dockerfile`

---

## 📄 License

MIT — free to use, modify, and distribute.

---

## 🙏 Credits

- [HuggingFace Transformers](https://huggingface.co/docs/transformers)
- [Sentence Transformers](https://www.sbert.net/)
- [Gradio](https://www.gradio.app/)
- Model: [`all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- Model: [`dslim/bert-base-NER`](https://huggingface.co/dslim/bert-base-NER)
