# Pull Request: Week 1 community contributions (asket)

## Title (for GitHub PR)

**Add: Week 1 notebooks and exercise (Frank Asket – asket)**

---

## Description

This PR adds my **Week 1** community contributions in `community-contributions/asket/`. All changes are confined to this folder; no files outside `community-contributions/` are modified.

### Author

**Frank Asket** ([@frank-asket](https://github.com/frank-asket)) – Founder & CTO building Human-Centered AI infrastructure.

---

## Contents

| File | Description |
|------|-------------|
| **day1.ipynb** | Day 1 lab (from week1): API setup, first LLM calls. Uses OpenRouter API key (`sk-or-`) where applicable. |
| **day2.ipynb** | Day 2 lab: Chat Completions API, OpenRouter endpoint, Gemini (optional), Ollama. Updated for OpenRouter (`base_url`, `sk-or-` key check). Includes **homework solution**: webpage summarizer with Ollama (self-contained cell with scraper path + model fallback). |
| **day4.ipynb** | Day 4 lab: Tokenizing with tiktoken, “memory” discussion. Uses OpenRouter client and `sk-or-` key validation. |
| **day5.ipynb** | Day 5 lab: **Company brochure builder** – selects relevant links from a site, fetches content, generates a markdown brochure via LLM. Configured for **OpenRouter** and default example **Klingbo** (https://klingbo.com). Path setup for `week1/scraper` when run from repo root or `asket/`. |
| **week1_EXERCISE.ipynb** | Week 1 exercise: (1) Technical Q&A tool with GPT + optional Ollama, streaming, code-fence-safe response cleaning; (2) **Bilingual website summarizer** (Ollama) for a URL – English + **Guéré** (Ivorian language), e.g. https://github.com/frank-asket. |
| **requirements-day2.txt** | Dependencies for Day 2 (python-dotenv, requests, openai). |
| **README.md** | Short intro and link to GUIDES_CHECKLIST. |
| **GUIDES_CHECKLIST.md** | Pre-PR checklist (guides, CONTRIBUTING, notebook/output limits). |

---

## Technical notes

- **API:** All notebooks that call an LLM use **OpenRouter** (`OPENROUTER_API_KEY`, `base_url="https://openrouter.ai/api/v1"`) and validate the key with the `sk-or-` prefix.
- **Scraper:** Day 2 (homework cell), Day 5, and week1_EXERCISE Part 2 add `sys.path` so `week1/scraper` (e.g. `fetch_website_contents`, `fetch_website_links`) works when run from repo root or from `community-contributions/asket/`.
- **Assets:** Image paths in markdown (e.g. `../../assets/resources.jpg`) are correct for the asket folder.
- **Brochure default:** Day 5 uses **Klingbo** (https://klingbo.com) as the default company for the brochure pipeline.

---

## Checklist

- [x] Changes are **only in `community-contributions/asket/`**.
- [ ] **Notebook outputs cleared** (please clear outputs before merging if required).
- [x] No changes to owner/main repo files outside this folder.
- [x] README and GUIDES_CHECKLIST included for contributors.

---

## How to run

1. From repo root: open any notebook, select the project kernel (e.g. `.venv`).
2. Set `OPENROUTER_API_KEY` in `.env` (and optionally `GOOGLE_API_KEY` for Day 2 Gemini).
3. For Ollama-based cells (Day 2 homework, week1_EXERCISE Part 2): run `ollama serve` and `ollama pull llama3.2` (or a variant; notebooks try multiple model tags).

Thanks for reviewing.
