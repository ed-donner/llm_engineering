# How to open your PR for this contribution

1. Commit only the new files under community-contributions (no changes to week1/day1.ipynb etc.):

   git add week1/community-contributions/idumachika/
   git status   # confirm only idumachika files are staged

2. Commit and push to your fork:

   git commit -m "Add Week 1 exercise solution: technical tutor (OpenRouter + Ollama)"
   git push myfork main

   (If your branch is something else, e.g. email-subject-line-suggester, use that branch and push it.)

3. On GitHub, open a PR from your fork (idumachika/llm_engineering) into ed-donner/llm_engineering.

4. Before submitting (course checklist): clear notebook outputs if needed, ensure only community-contributions changed.

Full guide: https://edwarddonner.com/pr

---

## PR criteria compliance (from HOW_TO_SUBMIT_PR.md)

| Criterion | Status |
|-----------|--------|
| Only changes under **community-contributions** | ✓ All files under `week1/community-contributions/idumachika/` |
| Notebook **outputs cleared** (or minimal) | ✓ Cells have `execution_count: null` and `outputs: []` |
| **Under 2,000 lines** total, not too many files | ✓ ~165 lines total; 3 files (notebook, README, this file) |
| No unnecessary test files, overly wordy README, or `.env.example` | ✓ No tests; README is 3 lines; no .env.example |
