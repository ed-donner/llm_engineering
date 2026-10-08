import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from trl import SFTTrainer, SFTConfig

def main():
    # 1. Load the dataset
    dataset_name = "ed-donner/items_prompts_lite"
    print(f"Loading dataset: {dataset_name}")
    dataset = load_dataset(dataset_name)
    
    # Check column names; if 'text' isn't there but there are instruction/response cols, we can format them.
    # The standard QLoRA setup often relies on a 'text' column, but we will adapt.
    train_dataset = dataset["train"]
    if "text" not in train_dataset.column_names:
        print("Formatting dataset into a 'text' column...")
        def format_prompt(example):
            # Fallback format if instruction/output format is used
            # Update these column names based on the actual dataset schema
            instruction = example.get("instruction", example.get("prompt", ""))
            response = example.get("output", example.get("completion", ""))
            return {"text": f"### Instruction:\n{instruction}\n\n### Response:\n{response}"}
        train_dataset = train_dataset.map(format_prompt)

    # 2. Configure BitsAndBytes for 4-bit quantization (QLoRA)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=False,
    )

    # 3. Load the base model and tokenizer
    # Using Llama-3.2-1B as mentioned in the exercise README. 
    # Note: Requires HuggingFace token and accepting terms.
    model_name = "meta-llama/Llama-3.2-1B"
    
    try:
        print(f"Attempting to load {model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto"
        )
    except Exception as e:
        print(f"Failed to load {model_name}. You may need to run `huggingface-cli login` and accept the Llama 3.2 license.")
        print(f"Falling back to Qwen2.5-0.5B... Error: {e}")
        model_name = "Qwen/Qwen2.5-0.5B"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto"
        )

    model = prepare_model_for_kbit_training(model)

    # 4. Configure LoRA (Low-Rank Adaptation)
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "v_proj"]
    )
    
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # 5. Set up Training Arguments
    training_args = SFTConfig(
        output_dir="./results",
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        optim="paged_adamw_32bit",
        save_steps=50,
        logging_steps=10,
        learning_rate=2e-4,
        weight_decay=0.001,
        fp16=False,
        bf16=False, # Set to True if using Ampere GPUs (e.g. A100, RTX 3090/4090)
        max_grad_norm=0.3,
        max_steps=100, # Keep small for initial test run
        dataset_text_field="text",
        max_length=256,
        packing=False,
    )

    # 6. Initialize SFTTrainer
    print("Initializing SFTTrainer...")
    trainer = SFTTrainer(
        model=model,
        train_dataset=train_dataset,
        processing_class=tokenizer,
        args=training_args,
    )

    # 7. Start Training
    print("Starting training...")
    trainer.train()

    # 8. Save the fine-tuned model
    print("Saving model to ./finetuned_price_model")
    trainer.save_model("./finetuned_price_model")
    tokenizer.save_pretrained("./finetuned_price_model")
    
    print("Fine-tuning complete!")

if __name__ == "__main__":
    main()
