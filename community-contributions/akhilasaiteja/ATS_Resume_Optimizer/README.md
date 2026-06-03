# ATS Resume Optimizer

An AI-powered resume optimization tool that scores 
your resume against a job description, rewrites 
bullets with JD-aligned vocabulary, and lets you 
refine your resume through multi-turn chat.

---

## What It Does

- Upload your resume (PDF or DOCX) and paste a job description
- Extract JD keywords and score your resume using a two-layer matching engine (exact + GPT semantic analysis)
- Rewrite existing bullets to incorporate JD vocabulary where your experience supports it
- Calculate a weighted ATS score across keyword coverage, relevant experience, and education match
- Identify missing technical skills vs soft skills — soft skills are excluded from scoring
- Refine your resume through an interactive chat interface that allows controlled updates, ensuring skills are only added when backed by user-confirmed experience
- Download the optimized resume as DOCX and PDF

---

## Tech Stack

Python, GPT-4o, Gradio, Docker, Hugging Face Spaces, GitHub Actions

---

## How to Run

```bash
pip install -r requirements.txt
echo "OPENAI_API_KEY=your_key_here" > .env
python app.py
```
