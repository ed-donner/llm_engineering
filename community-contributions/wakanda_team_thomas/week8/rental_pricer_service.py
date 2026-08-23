import modal

app = modal.App("rental-pricer-service")

image = (
    modal.Image.debian_slim()
    .pip_install(
        "torch",
        "transformers",
        "peft",
        "bitsandbytes",
        "accelerate",
        "datasets",
        "huggingface_hub",
    )
)


# --- Training ---

volume = modal.Volume.from_name("rental-pricer-checkpoints", create_if_missing=True)

@app.function(
    image=image,
    gpu="T4",
    timeout=14400,
    retries=3,
    volumes={"/checkpoints": volume},
    secrets=[modal.Secret.from_name("huggingface-secret")],
)
def train():
    import torch
    from datasets import load_dataset
    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        BitsAndBytesConfig,
        TrainingArguments,
        Trainer,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    MODEL_NAME = "meta-llama/Llama-3.2-3B"
    DATASET_NAME = "Gasmyr/rental-prices"
    OUTPUT_DIR = "/checkpoints/rental-pricer-finetuned"
    HUB_MODEL = "Gasmyr/rental-pricer"

    # Load dataset
    dataset = load_dataset(DATASET_NAME, split="train")
    dataset = dataset.train_test_split(test_size=0.1, seed=42)

    # Format for training: input -> expected rent
    def format_example(row):
        prompt = (
            f"Estimate the monthly rent in USD for this property:\n"
            f"{row['bedrooms']}-bedroom, {row['sqft']} sqft in {row['city']}. "
            f"{row['description']}\n"
            f"Estimated rent: ${row['rent']:.2f}"
        )
        return {"text": prompt}

    train_data = dataset["train"].map(format_example)
    test_data = dataset["test"].map(format_example)

    # Quantization config (4-bit)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
    )
    model = prepare_model_for_kbit_training(model)

    # LoRA config
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Tokenize
    def tokenize(example):
        tokens = tokenizer(
            example["text"],
            truncation=True,
            max_length=256,
            padding="max_length",
        )
        tokens["labels"] = tokens["input_ids"].copy()
        return tokens

    train_tokenized = train_data.map(tokenize, remove_columns=train_data.column_names)
    test_tokenized = test_data.map(tokenize, remove_columns=test_data.column_names)

    # Training
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=3,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        gradient_accumulation_steps=2,
        learning_rate=2e-4,
        warmup_steps=100,
        logging_steps=50,
        eval_strategy="steps",
        eval_steps=200,
        save_strategy="steps",
        save_steps=200,
        save_total_limit=2,
        fp16=True,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_tokenized,
        eval_dataset=test_tokenized,
    )

    # Resume from checkpoint if preempted
    import os
    last_checkpoint = None
    if os.path.isdir(OUTPUT_DIR):
        checkpoints = [d for d in os.listdir(OUTPUT_DIR) if d.startswith("checkpoint-")]
        if checkpoints:
            last_checkpoint = os.path.join(OUTPUT_DIR, sorted(checkpoints, key=lambda x: int(x.split("-")[1]))[-1])
            print(f"Resuming from checkpoint: {last_checkpoint}")

    trainer.train(resume_from_checkpoint=last_checkpoint)
    volume.commit()

    # Push to HuggingFace Hub
    model.push_to_hub(HUB_MODEL)
    tokenizer.push_to_hub(HUB_MODEL)
    print(f"Model pushed to https://huggingface.co/{HUB_MODEL}")


# --- Inference Service ---

@app.function(
    image=image,
    gpu="T4",
    timeout=120,
    secrets=[modal.Secret.from_name("huggingface-secret")],
)
def estimate_rent(description: str) -> float:
    import re
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    from peft import PeftModel

    BASE_MODEL = "meta-llama/Llama-3.2-3B"
    PEFT_MODEL = "Gasmyr/rental-pricer"

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
    )
    model = PeftModel.from_pretrained(base_model, PEFT_MODEL)

    prompt = f"Estimate the monthly rent in USD for this property:\n{description}\nEstimated rent: $"

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output = model.generate(**inputs, max_new_tokens=20, temperature=0.1)

    result = tokenizer.decode(output[0], skip_special_tokens=True)
    # Extract the price after "Estimated rent: $"
    match = re.search(r"Estimated rent: \$([\d,]+\.?\d*)", result)
    if match:
        return float(match.group(1).replace(",", ""))
    return 0.0
