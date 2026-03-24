"""
Modal-hosted Llama pricing service for Week 8 "Price is Right".

Uses your Week 7 fine-tuned Llama 3.2 3B. Deploy with:
    cd week8 && modal deploy community_contributions/winniekariuki/pricer_service.py
"""

import modal
from modal import Image, Volume

app = modal.App("pricer-service")
image = Image.debian_slim().pip_install(
    "torch", "transformers", "bitsandbytes", "accelerate", "peft"
)
secrets = [modal.Secret.from_name("huggingface-secret")]
hf_cache_volume = Volume.from_name("hf-hub-cache", create_if_missing=True)

GPU = "T4"
CACHE_DIR = "/cache"
BASE_MODEL = "meta-llama/Llama-3.2-3B"
HF_USER = "winniekariuki"
PROJECT_NAME = "price"
RUN_NAME = "2025-03-03-lite"  # Update with your actual run name from Week 7
FINETUNED_MODEL = f"{HF_USER}/{PROJECT_NAME}-{RUN_NAME}"
REVISION = None
MIN_CONTAINERS = 0

PREFIX = "Price is $"
QUESTION = "What does this cost to the nearest dollar?"


@app.cls(
    image=image.env({"HF_HUB_CACHE": CACHE_DIR}),
    secrets=secrets,
    gpu=GPU,
    timeout=1800,
    min_containers=MIN_CONTAINERS,
    volumes={CACHE_DIR: hf_cache_volume},
)
class Pricer:
    @modal.enter()
    def setup(self):
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        from peft import PeftModel

        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
        )
        self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL, quantization_config=quant_config, device_map="auto"
        )
        if REVISION:
            self.model = PeftModel.from_pretrained(base_model, FINETUNED_MODEL, revision=REVISION)
        else:
            self.model = PeftModel.from_pretrained(base_model, FINETUNED_MODEL)

    @modal.method()
    def price(self, description: str) -> float:
        import re
        import torch
        from transformers import set_seed

        set_seed(42)
        prompt = f"{QUESTION}\n\n{description}\n\n{PREFIX}"
        inputs = self.tokenizer.encode(prompt, return_tensors="pt").to("cuda")
        with torch.no_grad():
            outputs = self.model.generate(inputs, max_new_tokens=8)
        decoded = self.tokenizer.decode(outputs[0])
        after_prefix = decoded.split(PREFIX)[-1].replace(",", "")
        match = re.search(r"[-+]?\d*\.\d+|\d+", after_prefix)
        return float(match.group()) if match else 0.0
