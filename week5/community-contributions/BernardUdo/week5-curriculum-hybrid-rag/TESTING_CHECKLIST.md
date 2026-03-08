# Week 5 Hybrid RAG - Test and Validation Checklist

## Purpose

Use this checklist to verify functionality, reliability, and commit readiness for:

- `curriculum_hybrid_rag.py`
- `week5_curriculum_hybrid_rag.ipynb`

The app should provide grounded answers from local knowledge files, attach citations, and always return an audit (including fallback mode).

## App Summary

- Ingests `.md` / `.txt` files from `week5/knowledge-base`
- Chunks and indexes content into local artifacts
- Uses hybrid retrieval (vector + keyword)
- Returns answer + local sources + optional online reference links
- Produces audit metrics:
  - `groundedness`
  - `completeness`
  - `citation_quality`
- Handles provider failure/credit issues with graceful fallback output

## Quick Setup

- [ ] Install dependencies  
      `pip install -r week5/community-contributions/BernardUdo/week5-curriculum-hybrid-rag/requirements.txt`
- [ ] Configure API key in `.env`  
      `OPENROUTER_API_KEY=...` (or `OPENAI_API_KEY` fallback)
- [ ] Confirm local KB exists  
      `week5/knowledge-base`

## Notebook Validation

Notebook path: `week5/community-contributions/BernardUdo/week5-curriculum-hybrid-rag/week5_curriculum_hybrid_rag.ipynb`

- [ ] Cell 1: environment + paths load successfully
- [ ] Cell 2: module import + assistant init works
- [ ] Cell 3: optional rebuild control behaves as expected
- [ ] Cell 4: safely loads existing index or builds if missing
- [ ] Cell 5: always prints all sections:
  - `QUESTION`
  - `ANSWER`
  - `SOURCES (LOCAL RAG)`
  - `ONLINE REFERENCES`
  - `AUDIT`

## Functional Tests

### 1) Founder Query
- [ ] Input: `Who founded Insurellm and when?`
- [ ] Expected:
  - answer includes founder/year
  - relevant sources listed
  - audit printed

### 2) Mission Query
- [ ] Input: `What is Insurellm core mission according to company docs?`
- [ ] Expected:
  - answer references mission/vision language
  - top sources include company docs (`culture`, `overview`, `careers`)

### 3) Public Web Reference Fallback
- [ ] Input: a niche/non-public entity question
- [ ] Expected:
  - if no Wikipedia match, search links are shown (Google + DuckDuckGo)

## Reliability Tests

### A) Low-Credit Provider Mode (`402`)
- [ ] Simulate/observe `402` from provider
- [ ] Expected:
  - no crash
  - answer still returned (fallback extractive local answer)
  - sources still returned
  - audit still returned (fallback audit)

### B) Index Reuse
- [ ] Run notebook twice without rebuild
- [ ] Expected:
  - index is loaded from artifacts
  - no unnecessary rebuild/API calls

## CLI Smoke Tests

- [ ] Index build  
      `python week5/community-contributions/BernardUdo/week5-curriculum-hybrid-rag/curriculum_hybrid_rag.py --source-dir week5/knowledge-base index`
- [ ] Single question  
      `python week5/community-contributions/BernardUdo/week5-curriculum-hybrid-rag/curriculum_hybrid_rag.py ask --question "Who founded Insurellm and when?"`
- [ ] Verify answer + sources + audit in terminal output

## Commit Quality Gate

- [ ] Notebook outputs cleared
- [ ] Script compiles  
      `python -m py_compile week5/community-contributions/BernardUdo/week5-curriculum-hybrid-rag/curriculum_hybrid_rag.py`
- [ ] No linter errors in project folder
- [ ] Secrets excluded from git (`.env` not tracked)
