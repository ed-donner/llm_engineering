# Pricer with Qwen 2.5 3B

Same **"Price is Right"** task and data as the instructor, but fine-tune **Qwen 2.5 3B** instead of Llama 3.2 3B. Compare results to the instructor's Llama runs.

## What this does

1. **Data** — Uses instructor's `ed-donner/items_prompts_lite` (same prompt/completion format).
2. **Base model** — `Qwen/Qwen2.5-3B` with QLoRA (4-bit + LoRA).
3. **Training** — Same pipeline as Week 7 (SFTTrainer, same-style hyperparameters); LoRA targets adapted for Qwen2.
4. **Evaluation** — Run the course evaluator on the test set; compare average error to instructor's Llama 3.2 3B (lite ~65.40, full ~39.85 from `results.ipynb`).

## How to run

- **Colab (recommended):** Open `pricer_qwen2_3b.ipynb` in Google Colab. Set secrets: `HF_TOKEN`; optional `WANDB_API_KEY`. Set `HF_USER` to your Hugging Face username (for saving the run). Run all cells (training takes a while on T4).
- **Local:** Install `torch`, `transformers`, `datasets`, `peft`, `trl`, `bitsandbytes`, `accelerate`. Use `HF_TOKEN` and optional `WANDB_API_KEY` in `.env` or env; in the notebook you can replace `userdata.get("HF_TOKEN")` with `os.environ["HF_TOKEN"]` if not on Colab.

After training, the last cells load the fine-tuned model, run evaluation on the test set, and print a short comparison to the instructor's Llama numbers.

## Comparison (reference)


| Model                      | Dataset | Avg error (from course) |
| -------------------------- | ------- | ----------------------- |
| Llama 3.2 3B (base 4-bit)  | —       | 110.72                  |
| Llama 3.2 3B fine-tuned    | lite    | 65.40                   |
| Llama 3.2 3B fine-tuned    | full    | 39.85                   |
| **Qwen 2.5 3B fine-tuned** | lite    | *(your run)*            |


Your notebook will fill in the Qwen row after you run evaluation.