# PR Ready Notes (Week 6 Contribution)

## Title suggestion

`Community contribution: BernardUdo Week6 Price Right Capstone (CLI + Notebook + Deploy)`

## Summary bullets

- Implements a full Week 6 capstone workflow in a reusable CLI (`plan`, `build`, `evaluate`, `prepare-finetune`, `start-finetune`, `status-finetune`, `deploy`).
- Adds a notebook runner (`week6_price_right_capstone.ipynb`) mapped to the project `.venv` kernel for reproducible execution.
- Adds production-style docs (`README.md`), test checklist (`TESTING_CHECKLIST.md`), and PR screenshot checklist.
- Refactors local modeling to NumPy-only regressors for reliability in constrained environments (no `scikit-learn` dependency).

## Test plan checklist

- [ ] Install deps from `requirements.txt`
- [ ] `plan` command runs successfully
- [ ] `build --lite-mode` creates model artifacts
- [ ] `evaluate --lite-mode` returns metrics JSON
- [ ] `prepare-finetune --lite-mode` writes train/validation JSONL
- [ ] `deploy` serves app locally
- [ ] Notebook cells run in `Python (.venv)` kernel

## Risk/notes

- Fine-tune start/status requires valid `OPENAI_API_KEY`.
- `HF_TOKEN` is optional for lite dataset access but recommended to avoid hub rate limits.
