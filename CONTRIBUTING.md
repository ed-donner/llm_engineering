# Contributing to LLM Engineering

Thank you for contributing. Your work adds value for everyone on the course and gives you recognition on GitHub.

## Quick links

- **Full guide (Git + GitHub + PR):** [guides/03_git_and_github.ipynb](guides/03_git_and_github.ipynb)
- **PR overview:** https://edwarddonner.com/pr

## Pulling the latest code

From the repo root in your terminal:

```bash
git fetch upstream
git merge upstream/main
```

If you don’t have `upstream` yet:

```bash
git remote add upstream https://github.com/ed-donner/llm_engineering.git
```

## Submitting a Pull Request

1. **Fork** the repo on GitHub and clone your fork.
2. **Create a branch:** `git checkout -b my-contribution`
3. **Make changes** only in `community-contributions/` (unless we’ve agreed otherwise).
4. **Commit and push:**
   ```bash
   git add community-contributions/your-project/
   git commit -m "Add: short description"
   git push origin my-contribution
   ```
5. **Open a Pull Request** on GitHub from your branch to `ed-donner/llm_engineering` main.

## Before you submit – checklist

- [ ] Changes are **only in `community-contributions/`** (unless we’ve discussed it).
- [ ] **Notebook outputs are clear.**
- [ ] **Under 2,000 lines** of code in total, and not too many files.
- [ ] No unnecessary test files, long READMEs, `.env.example`, emojis, or other LLM artifacts.

Thanks!
