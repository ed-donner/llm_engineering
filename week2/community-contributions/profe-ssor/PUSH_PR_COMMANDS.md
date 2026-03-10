# Push to community contributions (open a PR)

Run these in your repo root (`~/projects/llm_engineering`).

## Option A: New branch for Week2 exercise only (recommended)

```bash
# Create and switch to a branch for this contribution
git checkout -b profe-ssor-week2-day-exercise

# Stage only your community contribution (3-way Ollama + GPT + Claude)
git add week2/community-contributions/profe-ssor/

# Commit
git commit -m "profe-ssor: Week2 day exercise - 3-way conversation (Ollama, GPT, Claude)"

# Push to your fork
git push myfork profe-ssor-week2-day-exercise
```

Then on GitHub:
1. Go to **https://github.com/profe-ssor/llm_engineering**
2. You should see “Compare & pull request” for `profe-ssor-week2-day-exercise`
3. Open the PR **into** `ed-donner/llm_engineering` (base: `main` or whatever the course uses)
4. Title example: **Community contribution: profe-ssor Week2 day exercise (3-way chat)**
5. Submit the PR

---

## Option B: Add to your current branch and push

If you prefer to keep everything on your current branch:

```bash
# Stage your community contribution
git add week2/community-contributions/profe-ssor/

# Commit
git commit -m "profe-ssor: Week2 day exercise - 3-way conversation (Ollama, GPT, Claude)"

# Push current branch to your fork
git push myfork
```

Then open a PR from that branch to `ed-donner/llm_engineering` as above.
