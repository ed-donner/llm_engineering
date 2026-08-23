# Week 7 – Evaluate a QLoRA Pricer Model (Najeeb)

Load a **pre-trained** Llama 3.2 3B model with QLoRA adapters and evaluate it on the "Price is Right" task: predict product price from description.

**Run in Colab (GPU):** [Open in Google Colab](https://colab.research.google.com/drive/1peU3XpnHNWhoTKLeo_w7E2kcGExt1hhH?usp=sharing)

## What's in this folder

- **`week7_exercise.ipynb`** – Notebook that:
  1. Loads the items_prompts dataset from HuggingFace (`ed-donner/items_prompts_lite` or `items_prompts_full`).
  2. Loads the base model with 4-bit or 8-bit QLoRA and attaches a pre-trained PEFT adapter from the Hub.
  3. Runs inference on the test set and evaluates using the shared `util.evaluate` harness (error, scatter plot, trend chart).

This notebook does **not** perform fine-tuning; it evaluates an already trained model.

## Requirements

- **GPU** (e.g. Colab T4/A100). For 3B with 4-bit QLoRA, ~10–16GB VRAM is typical.
- **Hugging Face token** with access to `meta-llama/Llama-3.2-3B` and to the adapter repo (default: `ed-donner/price-2025-11-30_15.10.55-lite` for lite mode).

## Setup

1. Set `HF_TOKEN` in your environment or in Colab Secrets.
2. In the notebook, set `HF_USER` to the Hugging Face user that hosts the adapter (default `ed-donner`). `LITE_MODE` chooses dataset and which adapter run to load.
3. Ensure `util.py` is available: uncomment the `wget` line in the first code cell to download it from the course repo when running in Colab.

## Data

Uses the same format as Week 7:

- **Prompt:** e.g. `"What does this cost to the nearest dollar?\n\n{summary}\n\nPrice is $"`
- **Completion:** e.g. `"42.00"`

The notebook uses the **test** split of `items_prompts_lite` (or `items_prompts_full`) and generates up to 8 new tokens per prompt.

## Model and adapter

- **Base model:** `meta-llama/Llama-3.2-3B` (set via `BASE_MODEL`).
- **Adapter:** Loaded from `{HF_USER}/{PROJECT_RUN_NAME}` (e.g. `ed-donner/price-2025-11-30_15.10.55-lite` when `LITE_MODE=True`). Optional `REVISION` is used in full mode.

Quantization is 4-bit (NF4) by default; set `QUANT_4_BIT = False` for 8-bit. bf16 is used when the GPU supports it.
