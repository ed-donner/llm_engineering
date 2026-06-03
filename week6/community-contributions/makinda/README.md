# Week 6 Community Contribution – Fine-tuning for "The Price is Right"

I fine-tuned **gpt-4.1-nano** on ed-donner's **items_lite** dataset, applying lessons from the week so the model performs better than the course baseline (zero-shot 62.51; course fine-tuned 75.91):

- **Parameters (inputs for price):** Structured product info — **Title, Category, Description, and Weight** when available (Day 2 + Day 3: structured text and weight help).
- **More data:** 100 train + 50 validation (Day 5).
- **Hyperparameters:** n_epochs=1, batch_size=1, **learning_rate_multiplier=0.5** (gentler to avoid overfitting; course fine-tuned did worse than zero-shot), seed=42.

## How to run

1. From the **repo root** (`llm_engineering`), open the notebook:
   ```bash
   jupyter notebook week6/community-contributions/makinda/week6_finetune_pricer.ipynb
   ```
   Or open it in VS Code/Cursor; the first cell adds `week6` to the path so `pricer` imports work.

2. Put in `.env` at the repo root:
   - `OPENAI_API_KEY` – for fine-tuning and inference
   - `HF_TOKEN` – to load `ed-donner/items_lite` from Hugging Face

3. Run all cells. After the job finishes, the last cell evaluates the fine-tuned model on the test set using the course evaluator.

## Evaluation results

Evaluation of the fine-tuned model on the test set (course evaluator):

| Metric | Value |
|--------|--------|
| **Average absolute error** | $143.36 |
| **MSE** | 223,625 |
| **R²** | -917.5% |

The model performed poorly compared to the course baselines (e.g. zero-shot GPT 4.1 Nano ~62.51, course fine-tuned ~75.91). The negative R² indicates predictions are worse than predicting the mean. Possible next steps: try different hyperparameters (e.g. learning rate, batch size), validate JSONL format and prompt consistency, or increase training data quality/size.

## Files

- **week6_finetune_pricer.ipynb** – Loads data, builds JSONL, uploads to OpenAI, starts the job, waits for completion, then evaluates.
- **config.py** – Dataset name, train/val sizes, base model, prompt text, and hyperparameters.
