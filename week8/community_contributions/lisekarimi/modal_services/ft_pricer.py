import modal
from modal import App, Volume, Image

import logging
logging.basicConfig(level=logging.INFO)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

GPU = "T4"  # Use a T4 GPU for inference
CACHE_PATH = "/cache"  # Mount point for the Modal volume

# Hugging Face model references
BASE_MODEL = "meta-llama/Meta-Llama-3.1-8B"
FINETUNED_MODEL = "ed-donner/pricer-2024-09-13_13.04.39"
REVISION = "e8d637df551603dc86cd7a1598a8f44af4d7ae36"  # Commit of the fine-tuned model

# Local cache paths (inside the volume)
BASE_MODEL_DIR = f"{CACHE_PATH}/llama_base_model"
FINETUNED_MODEL_DIR = f"{CACHE_PATH}/llama_finetuned_model"

# ─────────────────────────────────────────────────────────────────────────────
# Structure
# ─────────────────────────────────────────────────────────────────────────────

# Container (App: llm-ft-pricer)
# ├── /app                                     ← Code + installed Python packages (from image)
# ├── /cache                                   ← Mounted Modal volume (`hf-hub-cache`)
# │   └── meta-llama/Meta-Llama-3.1-8B/...     ← HuggingFace model files downloaded via snapshot_download



QUESTION = "How much does this cost to the nearest dollar?"
PREFIX = "Price is $"  # Used to parse generated output

# ─────────────────────────────────────────────────────────────────────────────
# Modal App, Image, Volume, Secrets
# ─────────────────────────────────────────────────────────────────────────────

app = modal.App("llm-ft-pricer")  # Define the Modal app

image = (
    Image.debian_slim()
    .pip_install("huggingface", "torch", "transformers", "bitsandbytes", "accelerate", "peft")  # All needed libraries
    .env({"HF_HUB_CACHE": CACHE_PATH})  # Hugging Face will store model files in /cache
)

cache_vol = modal.Volume.from_name("hf-hub-cache", create_if_missing=True)  # Persisted volume for caching models
secrets = [modal.Secret.from_name("HF_TOKEN")]  # Hugging Face auth token

# ─────────────────────────────────────────────────────────────────────────────
# Modal Class: Pricer
# ─────────────────────────────────────────────────────────────────────────────

# All methods in this class run inside the container with the image, volume, secrets, and GPU you configured.
@app.cls(
    image=image,
    secrets=secrets,
    volumes={CACHE_PATH: cache_vol},  # Mount volume into /cache
    gpu=GPU,
    timeout=1800,                     # 30-minute max runtime
    min_containers=0,                 # = 1 : Keeping one container warm uses credits continuously if you forget to stop it.
    scaledown_window=300,            # Shuts down the container
)
class Pricer:
    @modal.enter()
    def setup(self):
        import os, torch
        import logging
        from huggingface_hub import snapshot_download
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        from peft import PeftModel

        # Create cache path if it doesn't exist
        os.makedirs(CACHE_PATH, exist_ok=True)
        
        # Download base and fine-tuned models into volume
        logging.info("Downloading base model...")
        snapshot_download(BASE_MODEL, local_dir=BASE_MODEL_DIR)
        
        logging.info("Downloading fine-tuned model...")
        snapshot_download(FINETUNED_MODEL, revision=REVISION, local_dir=FINETUNED_MODEL_DIR)
        
        # Quantization config (4-bit)
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_type="nf4"
        )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_DIR)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        
        # Load base model (quantized)
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_DIR,
            quantization_config=quant_config,
            device_map="auto"
        )
        
        # Apply fine-tuned weights
        self.fine_tuned_model = PeftModel.from_pretrained(
            base_model,
            FINETUNED_MODEL_DIR,
            revision=REVISION
        )
        self.fine_tuned_model.generation_config.pad_token_id = self.tokenizer.pad_token_id
        
    @modal.method()
    def price(self, description: str) -> float:
        import re, torch
        from transformers import set_seed

        set_seed(42)  # Deterministic output

        # Construct prompt
        prompt = f"{QUESTION}\n\n{description}\n\n{PREFIX}"
        inputs = self.tokenizer.encode(prompt, return_tensors="pt").to("cuda")
        attention_mask = torch.ones(inputs.shape, device="cuda")

        # Generate model output (max 5 tokens)
        outputs = self.fine_tuned_model.generate(
            inputs,
            attention_mask=attention_mask,
            max_new_tokens=5,
            num_return_sequences=1
        )
        result = self.tokenizer.decode(outputs[0])

        # Extract number after "Price is $"
        contents = result.split("Price is $")[1]
        contents = contents.replace(',', '')
        match = re.search(r"[-+]?\d*\.\d+|\d+", contents)
        return float(match.group()) if match else 0  # Return parsed price or 0 if not found


