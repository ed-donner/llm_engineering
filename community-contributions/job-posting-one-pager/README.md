# Job posting → one-pager

Turn a job ad into a structured **one-pager** for your application: role summary, key requirements, suggested cover letter bullets, and keywords to include in your resume.

Inspired by week1 (scrape/fetch + LLM). Supports:

- **URL**: Scrape a job page (company careers, Greenhouse, etc.).
- **Pasted text**: Paste the full description (e.g. from LinkedIn) when the page is behind a login or hard to scrape.

## Setup

Uses the main repo environment. From repo root:

```bash
cd community-contributions/job-posting-one-pager
```

Ensure `.env` at repo root (or in this folder) has:

```
OPENAI_API_KEY=your_key_here
```

Dependencies are in the main `pyproject.toml` (openai, beautifulsoup4, requests, python-dotenv).

## Usage

### Jupyter notebook (recommended)

```bash
# from repo root
jupyter notebook community-contributions/job-posting-one-pager/job_one_pager.ipynb
```

Run the cells: set a `url` or `pasted_job` text, then call `generate_one_pager(...)` and display with `Markdown()`.

### Python

```python
from one_pager import generate_one_pager

# From URL
one_pager = generate_one_pager("https://company.com/careers/role")

# From pasted text (e.g. LinkedIn)
one_pager = generate_one_pager("""
Senior Engineer – Backend
Company X – Remote
Requirements: 5+ years Python...
""")

print(one_pager)
# Or save: open("one_pager.md","w").write(one_pager)
```

### Command line

From this directory:

```bash
# URL
python -m one_pager "https://example.com/job"

# Pasted text from stdin
echo "Paste job description here..." | python -m one_pager
```

Or paste directly (no URL):

```bash
python -m one_pager "Senior Engineer. Requirements: 5+ years..."
```

## Output sections

The one-pager includes:

- **Role summary** – 2–3 sentences on level and focus
- **Key requirements** – Must-haves from the posting
- **Nice-to-haves** – Preferred skills/experience
- **Suggested cover letter bullets** – 3–5 “why I fit” points, first person
- **Keywords to include in resume** – Terms to mirror from the ad

## Notes

- LinkedIn and some job boards block or restrict scraping; use **pasted text** for those.
- Long postings are truncated to 8,000 characters to stay within context limits.
- Model default: `gpt-4o-mini`. Override with `generate_one_pager(..., model="gpt-4o")` if needed.
