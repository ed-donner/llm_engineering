# Africa Flight Price Fine-tuning with QLoRA

This fine-tunes an **open-source Llama model** using **QLoRA** on the **Africa flight prices** dataset, building on the **week 6** [adeyemi-kayode](https://github.com/karosi12) assessment (GPT-4o mini fine-tuning). The goal is to produce a small, efficient model that can compete with frontier-style behavior on the task: *given a route, respond with the flight price in USD.*

---

## Links

| Resource | URL |
|----------|-----|
| **Dataset** | [Karosi/africa-flight-prices](https://huggingface.co/datasets/Karosi/africa-flight-prices) (Hugging Face) |
| **Experiment tracking** | [Weights & Biases – adekayor-karosi](https://wandb.ai/adekayor-karosi) |
| **Week 6 baseline** | `week6/community-contributions/adeyemi-kayode` (GPT-4o mini fine-tuning) |

---

## Contents

- **`africa_flight_qlora.ipynb`** – End-to-end notebook: load data, set up QLoRA, train Llama, run inference.
- **`README.md`** – This file (process overview and explanations).

---

## Process overview

1. **Data**  
   Load [Karosi/africa-flight-prices](https://huggingface.co/datasets/Karosi/africa-flight-prices) from the Hugging Face Hub. Each row has `origin_country`, `origin_city`, `destination_country`, `destination_city`, and `price_usd`. Split into train/validation (e.g. 85% / 15%).

2. **Format for SFT**  
   Each example is turned into a single text string:  
   `"What is the flight price from {origin_city}, {origin_country} to {destination_city}, {destination_country}? Respond with the price in USD only, no explanation. Answer: ${price:.2f}"`  
   The substring **` Answer: $`** is used as the **response template** so that the loss is computed only on the price part (via `DataCollatorForCompletionOnlyLM`).

3. **Base model**  
   **Llama** (e.g. `meta-llama/Llama-3.2-3B`). The notebook uses the Hugging Face `transformers` API; you need **HF_TOKEN** and access to the gated Llama model on the Hub.

4. **QLoRA (Quantized Low-Rank Adaptation)**  
   - **Quantization:** The base model is loaded in **4-bit** using `BitsAndBytesConfig` (NF4, double quant, compute in bfloat16). This greatly reduces memory so that a 3B model can be fine-tuned on a single consumer GPU.  
   - **LoRA:** Instead of updating all weights, we add **Low-Rank Adapters** to a subset of linear layers (`q_proj`, `v_proj`, `k_proj`, `o_proj`). Only these adapter parameters are trained; the rest of the model stays frozen (in quantized form).  
   - **QLoRA** = 4-bit quantized base + LoRA adapters. Training uses the quantized forward pass and updates only the LoRA parameters, with gradient checkpointing and 8-bit paged Adam for stability and memory efficiency.

5. **LoRA hyperparameters (typical)**  
   - **r** (rank): 16 – size of the low-rank matrices.  
   - **lora_alpha**: 32 – scaling of the LoRA update (often `2 * r`).  
   - **lora_dropout**: 0.05 – dropout in the adapter layers.  
   - **target_modules**: `["q_proj", "v_proj", "k_proj", "o_proj"]` – attention projection layers in the transformer.

6. **Training hyperparameters (SFTConfig)**  
   - **Epochs**: 3 (small dataset).  
   - **Batch size**: 4 per device, gradient accumulation 2 → effective batch size 8.  
   - **Learning rate**: 2e-4 with **cosine** schedule and **warmup_ratio** 0.05.  
   - **Optimizer**: `paged_adamw_8bit`.  
   - **Precision**: bf16; gradient checkpointing enabled.  
   - **Max sequence length**: 128 (enough for one Q&A).  
   - **Save / eval / log**: e.g. every 25 steps; keep last 2 checkpoints.

7. **Weights & Biases**  
   Runs are logged to the **adekayor-karosi** entity, project **africa-flight-qlora** (configurable in the notebook). Set **WANDB_API_KEY** in your environment (or `.env`) so the notebook can log training and validation metrics.

8. **Output**  
   The notebook saves the **LoRA adapters** and tokenizer under a local directory (e.g. `africa-flight-qlora-output`). You can load the base model in 4-bit and then apply these adapters with `peft.PeftModel.from_pretrained(...)` for inference, or merge and push to the Hub if desired.

9. **Inference**  
   A short inference example in the notebook shows how to call the fine-tuned model with a question and parse the **Answer: $…** part from the generated text.

---

## Why QLoRA and LoRA?

- **LoRA** keeps the base model frozen and trains only small adapter matrices. This reduces trainable parameters and overfitting risk, and makes it easy to swap adapters for different tasks.  
- **QLoRA** adds 4-bit quantization of the base model so that much larger models (e.g. 3B–8B) can be fine-tuned on limited GPU memory while still achieving competitive performance.  
Together, they let you “compete with frontier” behavior on a narrow task (Africa flight prices) using an open-source Llama model and a small, focused dataset.

---

## Setup

1. **Environment**  
   From repo root or this folder:
   ```bash
   pip install datasets transformers torch peft bitsandbytes trl accelerate wandb python-dotenv
   ```

2. **Secrets**  
   - **HF_TOKEN**: Hugging Face token (for gated Llama and dataset access).  
   - **WANDB_API_KEY**: Weights & Biases API key for [adekayor-karosi](https://wandb.ai/adekayor-karosi).  
   Prefer storing them in a `.env` file (or Colab secrets) and loading with `python-dotenv` as in the notebook.

3. **Hardware**  
   A GPU with enough VRAM for Llama-3.2-3B in 4-bit (typically 6–8 GB). For larger Llama variants, use a higher-memory GPU or Colab.

4. **Run**  
   Open `africa_flight_qlora.ipynb` and run all cells in order.
5. **Quick Note**
   Due to system/project requirement google colab is used to fine tune this project

---

## Summary

| Step | What happens |
|------|----------------|
| Data | Load Karosi/africa-flight-prices → train/val split → format as "Question … Answer: $X.XX" |
| Model | Llama (e.g. 3.2-3B) loaded in 4-bit (QLoRA) |
| PEFT | LoRA adapters on `q_proj`, `v_proj`, `k_proj`, `o_proj` |
| Training | SFTTrainer + DataCollatorForCompletionOnlyLM(" Answer: $"); metrics to W&B |
| Output | Adapters + tokenizer saved locally; optional Hub push |
| Inference | Generate from prompt; extract price from " Answer: $…" |

This gives you a reproducible pipeline to fine-tune an open-source Llama with QLoRA on your Africa flight price dataset and track experiments at [wandb.ai/adekayor-karosi](https://wandb.ai/adekayor-karosi).
