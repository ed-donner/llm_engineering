"""
Financial fraud detector for fintech.

Predicts whether a transaction is fraudulent or not, with confidence level and a short
helpful reason. Uses a fine-tuned LLM on bank transaction data from HuggingFace.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

os.environ["TOKENIZERS_PARALLELISM"] = "false"

from dotenv import load_dotenv
from datasets import load_dataset, Dataset
from huggingface_hub import login
from openai import OpenAI
from sklearn.model_selection import train_test_split
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model, PeftModel, TaskType
from trl import SFTTrainer

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OPENROUTER_URL = "https://openrouter.ai/api/v1"
TRAIN_SIZE = 50
VAL_SIZE = 20
TEST_SIZE = 30
RANDOM_STATE = 42
MODEL_NAME = "unsloth/Llama-3.2-1B-Instruct"
BASE_MODEL_OPENROUTER = "meta-llama/llama-3.2-1b-instruct"
LORA_SAVE_PATH = "./fraud_detector_lora"
SYSTEM_PROMPT = (
    "Analyze this bank transaction. Reply with: Fraudulent or Legitimate, "
    "Confidence: X%, Reason: short explanation."
)

# ---------------------------------------------------------------------------
# Secrets / API clients (supports Colab userdata or env vars)
# ---------------------------------------------------------------------------
def _get_secret(key: str, alt_key: str | None = None) -> str | None:
    """Get secret from Colab userdata or environment variable."""
    try:
        from google.colab import userdata
        try:
            val = userdata.get(key, None)
            if val:
                return val
            if alt_key:
                return userdata.get(alt_key, None)
        except Exception:
            pass
    except ImportError:
        pass
    val = os.getenv(key)
    if val:
        return val
    return os.getenv(alt_key) if alt_key else None


HF_TOKEN = _get_secret("HF_TOKEN")
OPENROUTER_API_KEY = _get_secret("OPENROUTER_API_KEY", "OPENAI_API_KEY")

if HF_TOKEN:
    login(HF_TOKEN, add_to_git_credential=True)

if OPENROUTER_API_KEY:
    openrouter_client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_URL)
else:
    openrouter_client = None

# ---------------------------------------------------------------------------
# Model state (set by load_finetuned_model)
# ---------------------------------------------------------------------------
ft_model = None
ft_tokenizer = None

# ---------------------------------------------------------------------------
# Data loading and preparation
# ---------------------------------------------------------------------------


def load_and_split_dataset() -> tuple[Any, Any, Any]:
    """Load qppd/bank-transaction-fraud and return train_df, val_df, test_df."""
    dataset = load_dataset("qppd/bank-transaction-fraud", split="train")
    df = dataset.to_pandas()
    df["is_fraud"] = (df["result"] != 0).astype(int)

    total_needed = TRAIN_SIZE + VAL_SIZE + TEST_SIZE
    subset, _ = train_test_split(
        df, train_size=total_needed, stratify=df["is_fraud"], random_state=RANDOM_STATE
    )
    train_df, rest = train_test_split(
        subset, train_size=TRAIN_SIZE, stratify=subset["is_fraud"], random_state=RANDOM_STATE
    )
    val_df, test_df = train_test_split(
        rest, train_size=VAL_SIZE, stratify=rest["is_fraud"], random_state=RANDOM_STATE
    )
    return train_df, val_df, test_df


def transaction_to_text(row: Any) -> str:
    """Convert a transaction row to a concise natural-language summary."""
    return (
        f"Transaction: {row['total_amount']:,.2f} amount, {row['transactions']} transactions, "
        f"{row['locations']} locations. Limit: {row['limit']:,}."
    )


def format_for_sft(item: dict) -> str:
    """Convert fraud item to chat format for Llama SFT."""
    label = "Fraudulent" if item["is_fraud"] else "Legitimate"
    conf = 85 if item["is_fraud"] else 92
    reason = "Suspicious pattern." if item["is_fraud"] else "Normal transaction pattern."
    assistant = f"{label}. Confidence: {conf}%. Reason: {reason}"
    return (
        f"### System:\n{SYSTEM_PROMPT}\n\n### User:\nIs this transaction fraudulent?\n\n"
        f"{item['text']}\n\n### Assistant:\n{assistant}"
    )


def prepare_training_data(
    train_df: Any, val_df: Any
) -> tuple[Dataset, Dataset, list[dict], list[dict]]:
    """Create train/val datasets and formatted data lists."""
    train_data = [
        {"text": transaction_to_text(row), "is_fraud": bool(row["is_fraud"])}
        for _, row in train_df.iterrows()
    ]
    val_data = [
        {"text": transaction_to_text(row), "is_fraud": bool(row["is_fraud"])}
        for _, row in val_df.iterrows()
    ]
    train_texts = [format_for_sft(d) for d in train_data]
    val_texts = [format_for_sft(d) for d in val_data]
    train_dataset = Dataset.from_dict({"text": train_texts})
    val_dataset = Dataset.from_dict({"text": val_texts})
    return train_dataset, val_dataset, train_data, val_data


# ---------------------------------------------------------------------------
# Model training
# ---------------------------------------------------------------------------


def train_model(
    train_dataset: Dataset,
    output_dir: str = LORA_SAVE_PATH,
) -> tuple[Any, Any]:
    """Load base model, add LoRA, train with SFTTrainer. Returns (model, tokenizer)."""
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    device_map = "auto" if torch.cuda.is_available() else None
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=(
            torch.bfloat16
            if (torch.cuda.is_available() or getattr(torch.backends, "mps", None) and getattr(torch.backends.mps, "is_available", lambda: False)())
            else torch.float32
        ),
        device_map=device_map,
    )

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,
        lora_alpha=16,
        lora_dropout=0.1,
        bias="none",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )
    model = get_peft_model(model, lora_config)
    model.tokenizer = tokenizer

    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=80,
        learning_rate=2e-4,
        bf16=torch.cuda.is_available() or (getattr(torch.backends, "mps", None) and getattr(torch.backends.mps, "is_available", lambda: False)()),
        logging_steps=10,
        save_strategy="steps",
        save_steps=40,
        save_total_limit=2,
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=train_dataset,
        args=training_args,
        dataset_text_field="text",
    )
    trainer.train()
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    return model, tokenizer


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------


def load_finetuned_model(path: str = LORA_SAVE_PATH) -> None:
    """Load fine-tuned model and tokenizer into module state."""
    global ft_model, ft_tokenizer
    ft_base = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
    )
    ft_model = PeftModel.from_pretrained(ft_base, path)
    ft_model.eval()
    ft_tokenizer = AutoTokenizer.from_pretrained(path)


def predict_finetuned(transaction_text: str) -> str:
    """Run fine-tuned model locally. Returns raw response string."""
    global ft_model, ft_tokenizer
    if ft_model is None or ft_tokenizer is None:
        load_finetuned_model()
    if not transaction_text:
        return "No input."
    prompt = (
        f"### System:\n{SYSTEM_PROMPT}\n\n### User:\nIs this transaction fraudulent?\n\n"
        f"{transaction_text}\n\n### Assistant:\n"
    )
    inputs = ft_tokenizer(prompt, return_tensors="pt").to(ft_model.device)
    with torch.no_grad():
        out = ft_model.generate(
            **inputs,
            max_new_tokens=80,
            do_sample=False,
            pad_token_id=ft_tokenizer.eos_token_id,
        )
    reply = ft_tokenizer.decode(
        out[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
    ).strip()
    return reply or "No response generated."


def predict_base_openrouter(transaction_text: str) -> str:
    """Call base model via OpenRouter. Returns raw response string."""
    if openrouter_client is None:
        return "OpenRouter not configured. Set OPENROUTER_API_KEY or OPENAI_API_KEY."
    user_msg = (
        f"Is this transaction fraudulent?\n\n{transaction_text}"
        if transaction_text
        else "No input."
    )
    resp = openrouter_client.chat.completions.create(
        model=BASE_MODEL_OPENROUTER,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=80,
        temperature=0,
    )
    return resp.choices[0].message.content.strip()


def compare_models(transaction_text: str) -> tuple[str, str]:
    """Call both fine-tuned (local) and base (OpenRouter). Returns (finetuned_response, base_response)."""
    ft_response = predict_finetuned(transaction_text)
    base_response = predict_base_openrouter(transaction_text)
    return ft_response, base_response


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def run_full_pipeline(lora_path: str = LORA_SAVE_PATH) -> None:
    """Load data, train, save model, and load for inference."""
    train_df, val_df, test_df = load_and_split_dataset()
    train_dataset, _, _, _ = prepare_training_data(train_df, val_df)
    model, tokenizer = train_model(train_dataset, output_dir=lora_path)
    load_finetuned_model(path=lora_path)


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
__all__ = [
    "SYSTEM_PROMPT",
    "transaction_to_text",
    "format_for_sft",
    "load_and_split_dataset",
    "prepare_training_data",
    "train_model",
    "load_finetuned_model",
    "predict_finetuned",
    "predict_base_openrouter",
    "compare_models",
    "run_full_pipeline",
]

if __name__ == "__main__":
    if Path(LORA_SAVE_PATH).exists() and (Path(LORA_SAVE_PATH) / "adapter_config.json").exists():
        load_finetuned_model()
    else:
        run_full_pipeline()
