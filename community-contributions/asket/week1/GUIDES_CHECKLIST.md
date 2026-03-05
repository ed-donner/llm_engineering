# Abiding by the repo guides

This checklist is based on **[../guides](../guides)** and **[CONTRIBUTING.md](../../CONTRIBUTING.md)**. Use it before submitting a PR or when working in notebooks.

---

## 1. Git and GitHub (guide 03, CONTRIBUTING)

- **Pull latest:** From repo root: `git fetch upstream` then `git merge upstream/main` (or `git rebase upstream/main`).
- **Upstream:** If missing, add: `git remote add upstream https://github.com/ed-donner/llm_engineering.git`
- **PR workflow:**
  1. Fork and clone your fork.
  2. Create a branch: `git checkout -b my-contribution`
  3. **Make changes only in `community-contributions/`** (e.g. this folder: `community-contributions/asket/`).
  4. Commit and push: `git add community-contributions/asket/` (or your path), `git commit -m "Add: short description"`, `git push origin my-contribution`
  5. Open a Pull Request on GitHub from your branch to `ed-donner/llm_engineering` main.

**Before you submit – checklist**

- [ ] Changes are **only in `community-contributions/`** (unless agreed with the maintainer).
- [ ] **Notebook outputs are cleared** (no saved execution output in .ipynb files).
- [ ] **Under 2,000 lines** of code in total, and not too many files.
- [ ] No unnecessary test files, long READMEs, `.env.example`, emojis, or other LLM clutter.

---

## 2. Notebooks (guide 05)

- Run cells **in order from the top** so the kernel has everything defined (avoids NameErrors – see guide 06).
- Use **Shift + Return** (or Shift + Enter) to run a cell.
- Select the correct **kernel** (e.g. `.venv` Python) via “Select Kernel” in the editor.

---

## 3. Python and debugging (guides 06, 08)

- **NameErrors:** Usually caused by not running earlier cells; run from the top or define the missing name.
- Use the **[troubleshooting](../../setup/troubleshooting.ipynb)** notebook in `setup/` if something fails.

---

## 4. Quick reference – guide index

| # | Topic |
|---|--------|
| 01 | Intro to guides |
| 02 | Command line |
| 03 | **Git and GitHub** (PRs, pull latest) |
| 04 | Technical foundations (env vars, APIs, uv) |
| 05 | **Notebooks** (running cells, kernel) |
| 06 | **Python foundations** (NameErrors, imports) |
| 07 | Vibe coding and debugging |
| 08 | Debugging techniques |
| 09 | APIs and Ollama |
| 10–14 | Intermediate Python, async, project start, frontend, Docker/Terraform |

All guides live in: **`guides/`** (e.g. `guides/03_git_and_github.ipynb`).
