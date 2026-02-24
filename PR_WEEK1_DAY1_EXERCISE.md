# Pull Request: asket contributions (community-contributions/asket only)

Use this as the **description** when you open the PR on GitHub.
All contributions go in **`community-contributions/asket/`** so the repo owner's files are never changed.

---

## Title

**Add community-contributions/asket: Day 1 email subject-line exercise**

---

## Description

### What

Adds **asket's contribution folder** `community-contributions/asket/` with a Week 1 Day 1 "try yourself" example: a small notebook that suggests a short email subject line from the email body (summarization use case from the main lab).

### Changes (all under community-contributions/asket — no other files touched)

- **`community-contributions/asket/day1-email-subject-line.ipynb`** — Self-contained notebook: load `.env` (OPENROUTER_API_KEY or OPENAI_API_KEY), then `suggest_subject(email_body)`. Outputs cleared.
- **`community-contributions/asket/README.md`** — Short note that this folder is asket's contributions only.

### Checklist (per course PR guidelines)

- [x] **Only changes in community-contributions** — this PR only adds files under `community-contributions/asket/`. No changes to the owner's repo (no week1/day1.ipynb, no other paths).
- [x] **Outputs cleared** — notebook has no saved outputs.
- [x] **Manageable size** — 2 small files, under 100 lines of code total.
- [x] No extra tests, .env.example, or emojis.

---

## How to open or update the PR

1. **Push the branch** (force-push, since history was rewritten):
   ```bash
   git push --force-with-lease origin week1-day1-email-subject-exercise
   ```

2. On GitHub, open your fork → **Pull requests**. Open a **New pull request** from `week1-day1-email-subject-exercise` into `ed-donner/llm_engineering` **main**.

3. Set **title** and **description** to the text above.

4. In **Files changed**, confirm: only `community-contributions/asket/README.md` and `community-contributions/asket/day1-email-subject-line.ipynb` are added (green only, no red). No changes outside this folder.

5. Submit the PR.
