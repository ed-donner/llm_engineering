# Clinical Triage Classifier — Week 7

Fine-tune Llama 3.2 3B with QLoRA to classify emergency department presentations by urgency level. A model that runs **fully offline** — no patient data ever leaves the hospital.

## What it does

Takes a brief clinical presentation and classifies it into one of four Manchester Triage System levels:
- **Immediate** — life-threatening, see now (chest pain + diaphoresis, unresponsive patient)
- **Urgent** — see within 30 minutes (high fever in infant, moderate dyspnoea)
- **Semi-urgent** — see within 1 hour (mild asthma, laceration requiring sutures)
- **Non-urgent** — can wait (minor cold symptoms, routine medication query)

## Why this matters

GPT-4.1-mini can do zero-shot triage classification, but it requires sending clinical descriptions to an external API — a problem in hospitals with strict data governance. A fine-tuned Llama model runs entirely on local hardware with no internet connection required.

## Results

| Model | Accuracy | Notes |
|---|---|---|
| Base Llama 3.2 3B (4-bit) | ~25% | Random — doesn't understand the task |
| GPT-4.1-mini zero-shot | ~72% | Good but requires internet + API cost |
| Fine-tuned Llama 3.2 3B | ~89% | Runs offline, zero inference cost |

## Notebook structure

The notebook runs on **Google Colab** with a T4 GPU (free tier).

1. **Part 1** — Generate 2000 synthetic triage cases with GPT-4.1-mini, push to HuggingFace Hub
2. **Part 2** — Load dataset, build prompts, inspect base model
3. **Part 3** — Fine-tune with QLoRA (BitsAndBytes 4-bit + LoRA adapters)
4. **Part 4** — Evaluate: accuracy, F1-score, confusion matrix
5. **Part 5** — Compare models + Gradio UI for interactive triage

## Setup

### 1. Open in Google Colab

Open `clinical_triage_classifier.ipynb` in Google Colab with a **T4 GPU** runtime.

### 2. Add secrets in Colab

In the Colab sidebar (key icon), add:
- `OPENAI_API_KEY` — for generating synthetic training data (Part 1 only)
- `HF_TOKEN` — HuggingFace token with write access

### 3. Run cells sequentially

Parts 1-2 run on CPU. Parts 3-5 require the T4 GPU.

## Data

Training data is generated in Part 1 and pushed to HuggingFace Hub — it is not stored in this repo. The fine-tuned model adapters are also pushed to your HuggingFace Hub (private repo).
