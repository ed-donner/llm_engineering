# Week 7 – "The Price is Right" fine-tuning (Colab)
# Goal: better price prediction with open-source QLoRA (beat base Llama ~110, aim for ~65 or lower).
# Dataset: ed-donner (Hugging Face). Models/artifacts: felixmakinda.

# Data: use instructor's dataset
HF_DATASET_USER = "ed-donner"
DATASET_NAME = "items_lite"  
DATASET = f"{HF_DATASET_USER}/{DATASET_NAME}"

# Felix Makinda's Hugging Face account for pushing trained model, adapters, or prompt datasets
HF_USER = "felixmakinda"
# Example: push fine-tuned model or adapter to felixmakinda/price-llama-qlora-lite
MODEL_REPO_ID = f"{HF_USER}/price-llama-qlora-lite"

# Base model (Week 7 style: open-source, QLoRA on Colab)
BASE_MODEL = "meta-llama/Llama-3.2-3B"
# Prompt settings (from week7 day2)
MAX_PROMPT_TOKENS = 110
DO_ROUND_PRICE = True


TRAIN_SUBSET = 3000   
VAL_SUBSET = 300
SEED = 42
