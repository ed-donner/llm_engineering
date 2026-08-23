# Fine-tune vs zero-shot

Compare **fine-tuned** vs **zero-shot** pricer on the same test set.  Has a few changes aimed at better accuracy, then evaluates both models with the course evaluator.

## What it does

1. **Load data** — `Item.from_hub("ed-donner/items_lite")`, then filter to items with valid price and non-empty text (summary or title).
2. **Fine-tune** — Prepare JSONL (200 train, 50 val), upload to OpenAI, create fine-tuning job (`gpt-4.1-nano-2025-04-14`, 2 epochs). Targets use cents (`$X.XX`); same prompt at train and eval.
3. **Predictors** — Fine-tuned model vs zero-shot `gpt-4o-mini` (same prompt).
4. **Compare** — Run `evaluate()` on each on 100 test items; compare average error and charts.

## Improvements over instructor baseline

- **Target format**: `$X.XX` (e.g. `$19.99`) instead of rounded `$X.00` so the model learns cent-level prices.
- **Data quality**: Only train/val on items with `price > 0` and non-empty (summary or title).
- **More data + epochs**: 200 training examples and 2 epochs (vs 100 and 1) for better learning on small data.
- **Consistent prompt**: Same user message and text source (summary or title) at training and inference.

## How to run

1. Set `**HF_TOKEN`** and `**OPENAI_API_KEY**` in `.env`.
2. Open `fine_tune_vs_zeroshot.ipynb`. Run from **fine_tune_vs_zeroshot/** so the path to `pricer` resolves.
3. Run all cells. Re-run the "Wait for job" cell until status is `succeeded`, then run the predictors and comparison cells.

## Requirements

- `openai`, `huggingface_hub`, `datasets`, `scikit-learn`, `python-dotenv`, `plotly`, `tqdm` (from repo `pyproject.toml`).

