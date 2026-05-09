# Job description one-pager – Gradio (Week 3)

Week 3 community contribution: **Job posting → one-pager** with a **synthetic job posting** flow (Week 3 synthetic data theme). Same idea as the [week 2 job-one-pager](../../week2/community-contributions/job-one-pager-gradio).

## What it does

- **Tab 1 – Paste job:** Paste a job URL or full description → pick model → **Generate one-pager** (role summary, requirements, cover letter bullets, resume keywords). Optional **Save as .md**.
- **Tab 2 – Synthetic job (Week 3):** Describe the role (e.g. *Senior backend engineer, fintech, 5+ years Python*) → **Generate synthetic job posting** (LLM creates a realistic fake job ad) → **Generate one-pager from this** → optionally Save.

## Week 3 connection

Tab 2 is a synthetic data generator for job postings: you describe the kind of role, the model generates a full fictional job ad, then the same one-pager pipeline runs on it.

## Setup

- `OPENROUTER_API_KEY` in `.env` (repo root or this folder).
- Dependencies in main repo `pyproject.toml` or use `requirements.txt` here.

## Run

**Notebook:** Open `job_one_pager_gradio.ipynb` and run all cells. App opens in your browser.

**CLI:** `python app.py` from this folder.
