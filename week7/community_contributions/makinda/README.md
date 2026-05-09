# Week 7 Community Contribution – makinda

**Goal:** Better price prediction using an open-source model (QLoRA fine-tuned Llama). Course benchmarks (results.ipynb): Base Llama 3.2 4-bit ~110, Fine-tuned Lite ~65, Fine-tuned Full ~40. We aim to improve on the base and get close to the fine-tuned benchmarks.

**Concepts used:** Week 7 (day1–day5: QLoRA, prompt data, base model, train, eval), Week 2 (day1–day2: APIs, env, HF), Week 2 day3 and 4, Week 1 Day 5 (full solution flow), and `week7/results.ipynb` (benchmarks).

## Where things live

| What                                           | Source                                                                                               |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Dataset**                                    | **ed-donner** on Hugging Face (`ed-donner/items_lite` or `items_full`) — read-only.                  |
| **Trained model / adapters / prompt datasets** | **felixmakinda** — personal Hugging Face account. All uploads (model repo, datasets you create) go here. |

## Running on Google Colab

The notebook is tuned for **free Colab with a T4 GPU** (~15GB VRAM): smaller batch size (2), sequence length (128), and train subset (3000) to avoid OOM and timeouts. With a A100 or paid Colab, we could increase `TRAIN_SUBSET`, `BATCH_SIZE`, and `MAX_SEQ_LENGTH` in the config/training cells.

1. **Open the notebook in Colab**  
   Upload `week7_makinda_colab.ipynb` to Colab, or clone the repo and open it from the `week7/community_contributions/makinda/` folder.

2. **Secrets (Colab)**  
   In Colab: **Secrets** (key icon in left sidebar) → add:
   - `HF_TOKEN` — the Hugging Face token (required to load `ed-donner` dataset and push to `felixmakinda`).
   - `WANDB_API_KEY` — your Weights & Biases API key (optional; if set, training loss and metrics are logged to W&B project `price-is-right-makinda`).

3. **Runtime**  
   **Runtime → Change runtime type → T4 GPU** (or A100 if available).  
   Run all cells. The notebook will:
   - Install dependencies (`datasets`, `transformers`, `torch`, `peft`, `bitsandbytes`, etc.)
   - Log in to Hugging Face
   - Load **ed-donner/items_lite**
   - Prepare prompt data (Week 7 Day 2 style)
   - Optionally run QLoRA fine-tuning and push the model to **felixmakinda** (e.g. `felixmakinda/price-llama-qlora-lite`)
   - Evaluate on the test set

## Config

Edit `config.py` (or the config cell in the notebook) to change:

- `DATASET` — always from **ed-donner** (e.g. `ed-donner/items_lite`).
- `HF_USER` / `MODEL_REPO_ID` — your HF user **felixmakinda**; model/artifacts are pushed here.
- `BASE_MODEL`, `TRAIN_SUBSET`, `MAX_PROMPT_TOKENS`, etc.

## Files

- **week7_makinda_colab.ipynb** — Main Colab notebook: load data (ed-donner), train (QLoRA), push (felixmakinda), evaluate.
- **config.py** — Dataset name, HF user, base model, and training defaults.
