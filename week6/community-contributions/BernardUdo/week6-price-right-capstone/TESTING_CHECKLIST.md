# Week 6 Price Is Right - Testing Checklist

Use this checklist to validate `week6_price_right_capstone.py` before sharing.

## Setup

- [ ] Install dependencies:
      `pip install -r week6/community-contributions/BernardUdo/week6-price-right-capstone/requirements.txt`
- [ ] Configure `.env` with `HF_TOKEN` and (if needed) `OPENAI_API_KEY`.

## Planning + Requirements

- [ ] `plan` command prints Day 1-5 requirements and build/deploy expectations.

Command:
`python week6/community-contributions/BernardUdo/week6-price-right-capstone/week6_price_right_capstone.py plan`

## Build + Baseline Validation

- [ ] Build runs successfully in lite mode.
- [ ] `artifacts/model_bundle.pkl` exists.
- [ ] `artifacts/metrics.json` exists and contains MAE/RMSE/R2/%within_20.

Command:
`python week6/community-contributions/BernardUdo/week6-price-right-capstone/week6_price_right_capstone.py build --lite-mode --train-size 12000 --val-size 3000`

## Evaluation

- [ ] Evaluate local model on test split.
- [ ] Metrics JSON output looks reasonable and non-empty.

Command:
`python week6/community-contributions/BernardUdo/week6-price-right-capstone/week6_price_right_capstone.py evaluate --lite-mode --test-size 1500`

## Fine-Tune Prep + Lifecycle

- [ ] JSONL files are generated under `artifacts/jsonl/`.
- [ ] `start-finetune` returns `job_id`.
- [ ] `status-finetune <job_id>` returns status + events.

Commands:
- `python week6/community-contributions/BernardUdo/week6-price-right-capstone/week6_price_right_capstone.py prepare-finetune --lite-mode --train-size 100 --val-size 50`
- `python week6/community-contributions/BernardUdo/week6-price-right-capstone/week6_price_right_capstone.py start-finetune`
- `python week6/community-contributions/BernardUdo/week6-price-right-capstone/week6_price_right_capstone.py status-finetune ftjob_...`

## Deployment Smoke Test

- [ ] Gradio app launches without errors.
- [ ] Product description input returns local estimate.
- [ ] If `FINE_TUNED_MODEL` is configured, fine-tuned estimate appears.

Command:
`python week6/community-contributions/BernardUdo/week6-price-right-capstone/week6_price_right_capstone.py deploy --host 127.0.0.1 --port 7866`

## Quality Gate

- [ ] Script compiles:
      `python -m py_compile week6/community-contributions/BernardUdo/week6-price-right-capstone/week6_price_right_capstone.py`
- [ ] No secrets committed (`.env` excluded, `.env.example` only).
