# Course PR Reviewer for `ed-donner/llm_engineering`

Paste any PR number from the course repo. The notebook fetches title, body, files, comments, and a truncated diff via the public GitHub API, then asks an LLM to review it against Ed’s community-contribution guidelines.

Works for **any week** (`community-contributions/` or `weekN/community-contributions/`).

## Run

1. Use the course `.venv` / `uv` environment
2. Ensure `OPENAI_API_KEY` is in `.env`
3. Open `day1_pr_reviewer.ipynb` and run all cells
4. Change `PR_NUMBER` to any open PR: https://github.com/ed-donner/llm_engineering/pulls

Optional: set `GITHUB_TOKEN` in `.env` for higher rate limits and for **posting** comments.

## Comments

1. **Display** — notebook loads existing PR conversation comments
2. **Post** — set `POST_COMMENT = True` to publish the suggested review comment

Posting needs a classic token with `public_repo` (or equivalent). If GitHub returns 403, copy the suggested comment and paste it on the PR manually.

## Sample PRs used while building this

| PR | Purpose |
| --- | --- |
| [#3662](https://github.com/ed-donner/llm_engineering/pull/3662) | Positive/smoke test — clean day1-style summarizer contribution |
| [#3663](https://github.com/ed-donner/llm_engineering/pull/3663) | Negative test — intentional guideline violations (wrong paths, secrets, outputs, clutter) |

Try `PR_NUMBER = 3662` or `3663` in the notebook to reproduce those reviews.
