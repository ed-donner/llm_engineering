# ATS Resume Optimizer

An AI-powered resume optimization tool that scores your resume against a job description, rewrites bullets with JD-aligned vocabulary, and lets you refine your resume through multi-turn chat.

Built with GPT-4o, Gradio, and deployed on Hugging Face Spaces with Docker.

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

| Component | Technology |
|-----------|------------|
| LLM | GPT-4o, GPT-4.1-mini |
| UI | Gradio |
| Resume Parsing | pdfplumber, pypdf, python-docx |
| PDF Generation | ReportLab |
| Deployment | Docker, Hugging Face Spaces |
| CI/CD | GitHub Actions |
| Testing | pytest (52 tests) |
| API Handling | OpenAI API (tool calling + multi-turn context management) |

---

## How to Run Locally

**1. Clone the repo:**

```bash
git clone https://github.com/saiteja0737/ats-resume-optimizer
cd ats-resume-optimizer
```

**2. Install dependencies:**

```bash
pip install -r requirements.txt
```

**3. Add your OpenAI API key:**

```bash
echo "OPENAI_API_KEY=your_key_here" > .env
```

**4. Run the app:**

```bash
python app.py
```

**5. Open in browser:**

```
http://127.0.0.1:7861
```

---

## How to Run with Docker

```bash
docker build -t ats-resume-optimizer .
docker run -p 7860:7860 \
  -e OPENAI_API_KEY=your_key_here \
  ats-resume-optimizer
```

---

## Project Structure

```
ats-resume-optimizer/
├── app.py
├── requirements.txt
├── Dockerfile
├── README.md
├── tests/
│   ├── __init__.py
│   ├── test_experience.py
│   ├── test_keyword.py
│   ├── test_scoring.py
```

---

## Architecture

```
Resume (PDF/DOCX) + Job Description
         ↓
   GPT-4o Optimization
   ├── Keyword extraction
   ├── Bullet rewriting with JD vocabulary
   └── Soft skill filtering
         ↓
   Two-layer Scoring Engine
   ├── Exact keyword matching
   ├── GPT semantic matching
   ├── Experience relevance classification
   └── Education match
         ↓
   Weighted ATS Score
   └── Keywords 50% + Experience 30% + Education 20%
         ↓
   Multi-turn Chat Refinement
   ├── User confirms missing skills
   ├── GPT adds to correct resume section
   └── Score recalculates after each update
         ↓
   Download DOCX + PDF
```

---

## Key Features

### Two-layer Keyword Scoring
Exact string matching for technical tools combined with GPT semantic analysis for domain concepts. Soft skills like "curious mindset" and "team player" are automatically excluded from scoring.

### Weighted ATS Score
Keywords (50%) + Relevant Experience (30%) + Education Match (20%). Experience is classified as full, partial, or none credit using GPT-4o based on role relevance.

### Chat-Based Resume Refinement with Experience Validation
Enables users to update their resume through a conversational interface. The system prevents adding unverified skills by requiring user confirmation, reducing the risk of over-claiming and improving interview readiness.

### 52 Passing Tests
Covers keyword scoring, experience parsing, date extraction, education matching, and output formatting.

This design ensures the resume is not only ATS-optimized but also aligned with what the candidate can confidently explain in interviews.
---

## Author

**Sai Teja Adusumilli**

- Portfolio: [saiteja0737.github.io/portfolio](https://saiteja0737.github.io/portfolio)
- LinkedIn: [linkedin.com/in/adsteja](https://linkedin.com/in/adsteja)
- GitHub: [github.com/saiteja0737](https://github.com/saiteja0737)
