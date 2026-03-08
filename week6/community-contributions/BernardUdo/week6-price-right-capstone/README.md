# Week 6 Community Contribution: Price Is Right Capstone

This contribution turns the Week 6 notebook flow (Day 1-5) into a reusable project you can run from CLI and deploy locally.

## What it requires (Day 1 to Day 5)

- **Day 1 - Data curation**
  - Load Amazon product metadata.
  - Keep valid pricing rows and clean noisy text.
- **Day 2 - Preprocessing**
  - Use standardized product summaries (`Item.summary`) for stronger modeling.
- **Day 3 - Baselines + evaluation**
  - Train classical models and evaluate with MAE, RMSE, R2, and `% within $20`.
- **Day 4 - Neural/LLM comparison**
  - Compare local model against model-based estimates and inspect failure modes.
- **Day 5 - Fine-tuning**
  - Generate OpenAI JSONL files, launch fine-tuning, and evaluate the tuned model.

## What this implementation includes

- `week6_price_right_capstone.py`:
  - `plan` command for requirements and execution map
  - `build` command to train a blended local pricing model (text + tabular features)
  - `evaluate` command for local and optional fine-tuned model
  - `prepare-finetune` command to create JSONL files
  - `start-finetune` and `status-finetune` commands for OpenAI fine-tuning lifecycle
  - `deploy` command to launch a Gradio app
- `requirements.txt` for dependencies
- `.env.example` for required environment variables
- `TESTING_CHECKLIST.md` for validation before commit/PR

## Setup

From repo root:

```bash
pip install -r week6/community-contributions/BernardUdo/week6-price-right-capstone/requirements.txt
```

Create `.env` and set keys:

```bash
HF_TOKEN=...
OPENAI_API_KEY=...
# optional:
FINE_TUNED_MODEL=ft:...
```

## Plan, Build, Evaluate, Deploy

### 1) Plan requirements

```bash
python week6/community-contributions/BernardUdo/week6-price-right-capstone/week6_price_right_capstone.py plan
```

### 2) Build local model

Lite mode is faster and lower resource:

```bash
python week6/community-contributions/BernardUdo/week6-price-right-capstone/week6_price_right_capstone.py build --lite-mode --train-size 12000 --val-size 3000
```

Artifacts:
- `artifacts/model_bundle.pkl`
- `artifacts/metrics.json`

### 3) Evaluate local model

```bash
python week6/community-contributions/BernardUdo/week6-price-right-capstone/week6_price_right_capstone.py evaluate --lite-mode --test-size 1500
```

Evaluate with fine-tuned model too:

```bash
python week6/community-contributions/BernardUdo/week6-price-right-capstone/week6_price_right_capstone.py evaluate --lite-mode --fine-tuned-model ft:...
```

### 4) Prepare and run fine-tuning

Prepare JSONL:

```bash
python week6/community-contributions/BernardUdo/week6-price-right-capstone/week6_price_right_capstone.py prepare-finetune --lite-mode --train-size 100 --val-size 50
```

Start job:

```bash
python week6/community-contributions/BernardUdo/week6-price-right-capstone/week6_price_right_capstone.py start-finetune --base-model gpt-4.1-nano-2025-04-14 --epochs 1
```

Check status:

```bash
python week6/community-contributions/BernardUdo/week6-price-right-capstone/week6_price_right_capstone.py status-finetune ftjob_...
```

### 5) Deploy locally (Gradio)

```bash
python week6/community-contributions/BernardUdo/week6-price-right-capstone/week6_price_right_capstone.py deploy --host 127.0.0.1 --port 7866
```

## Notes

- The local model is a practical baseline blend:
  - token-frequency linear model (NumPy ridge) over product text
  - lightweight tabular ridge on weight + text-length signals
- Fine-tune commands require `OPENAI_API_KEY`.
- Deployment works with local model only, or local + fine-tuned model when configured.
