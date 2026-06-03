# Week 7 Exercise – Fine-Tune Llama 3.2 3B with QLoRA (winniekariuki)

**Builds on Week 6:** In Week 6 we predicted product prices from `ed-donner/items_lite` using constant baseline and LLM (GPT-4o-mini). Here we **fine-tune** Llama 3.2 3B with QLoRA, then evaluate on the same task.

**Run in Colab:** [Open in Google Colab](https://colab.research.google.com/drive/1EjbGSjHeYeKBKwN5guVA2utADf41CH5U#scrollTo=hDIKhG8VVMGZ)

## What's included

1. **Training**
   - Load Llama 3.2 3B with 4-bit quantization
   - QLoRA (LoRA on attention layers) with SFTTrainer
   - Data: `ed-donner/items_prompts_lite`
   - Adapters saved to `output_dir` (optionally push to Hub)

2. **Evaluation**
   - Same format as Week 6: MAE, R², scatter and error-trend charts via `util.evaluate()`

## How to run

1. Open `week7_exercise.ipynb` in **Google Colab** (GPU required, e.g. T4)
2. Add `HF_TOKEN` to Colab secrets (key icon in sidebar)
3. Run all cells (setup cell installs deps and downloads `util.py`)
4. Set `HF_USER` to your HuggingFace username if you want to push adapters to the Hub

## Dependencies

- `bitsandbytes`, `trl`, `transformers`, `accelerate`, `datasets`, `peft`
- `util.py` from the course repo (downloaded by the setup cell)
- **HF_TOKEN** with access to `meta-llama/Llama-3.2-3B` (gated; accept the license at [huggingface.co](https://huggingface.co/meta-llama/Llama-3.2-3B))
