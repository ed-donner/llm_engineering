# Week 6 Exercise – The Price is Right (winniekariuki)

Product price predictor from description. Uses `ed-donner/items_lite` from HuggingFace, constant baseline + LLM (GPT-4o-mini), and `pricer.evaluator.evaluate()`.

## What's included

- Load train/val/test from HuggingFace
- Constant baseline (mean price) + LLM baseline
- Evaluation with course `evaluate()` metric
- Gradio UI: paste description → estimated price

## How to run

1. From repo root or `week6/`: ensure `OPENAI_API_KEY` in `.env` (dataset is public; HF_TOKEN not required)
2. Open `week6_exercise.ipynb` and run all cells
3. Gradio app launches at the end

## Dependencies

Uses course stack: `openai`, `huggingface_hub`, `gradio`, `python-dotenv`, and the `pricer` package in `week6/`.
