"""
pricer_modal.py

Deploys the fine-tuned Qwen2.5-3B price estimator as a Modal cloud service.
The model loads ONCE when the container starts and stays warm between calls —
no re-downloading on every run.

To deploy:
    modal deploy pricer_modal.py

To test from terminal:
    modal run pricer_modal.py

Requirements:
    pip install modal
    modal setup                          # login to Modal
    modal secret create huggingface-secret HF_TOKEN=hf_your_token_here
"""

import modal
from modal import Volume, Image

# ── Modal app setup ───────────────────────────────────────────────────────────
app   = modal.App("smart-deal-pricer")
image = Image.debian_slim().pip_install(
    "torch", "transformers", "bitsandbytes", "accelerate", "peft"
)
secrets = [modal.Secret.from_name("huggingface-secret")]

# ── Model config ──────────────────────────────────────────────────────────────
# Trained by Geraldino07 on 20,000 product price examples using QLoRA
# To use your own model replace these three values
BASE_MODEL    = "Qwen/Qwen2.5-3B"
HF_MODEL_REPO = "Geraldino07/price-2026-03-09_21.46.47"
HF_REVISION   = "285f0bdd4a8f6f30d6f6af59976e69ecc7d4688c"

# ── Infrastructure ────────────────────────────────────────────────────────────
GPU       = "T4"
CACHE_DIR = "/cache"

# MIN_CONTAINERS = 1  keeps container always warm (costs ~$1.50/day on T4)
# MIN_CONTAINERS = 0  container goes cold after 2 mins idle (free, but cold start ~3 mins)
MIN_CONTAINERS = 0

PREFIX   = "Price is $"
QUESTION = "What does this cost to the nearest dollar?"

# Persistent volume — model weights cached here so they don't re-download
hf_cache_volume = Volume.from_name("hf-hub-cache", create_if_missing=True)


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
        """
        Runs ONCE when the container starts.
        Model stays in memory for all subsequent .price() calls.
        """
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
        self.tokenizer.pad_token    = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"

        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            quantization_config=quant_config,
            device_map="auto",
        )
        self.model = PeftModel.from_pretrained(
            base_model,
            HF_MODEL_REPO,
            revision=HF_REVISION,
        )

    @modal.method()
    def price(self, description: str) -> float:
        """
        Estimate the market price of a product from its description.
        Called remotely from pricer_agent.py via Modal client.
        """
        import re
        import torch
        from transformers import set_seed

        set_seed(42)
        prompt = f"{QUESTION}\n\n{description}\n\n{PREFIX}"
        inputs = self.tokenizer.encode(prompt, return_tensors="pt").to("cuda")

        with torch.no_grad():
            outputs = self.model.generate(inputs, max_new_tokens=5)

        result   = self.tokenizer.decode(outputs[0])
        contents = result.split(PREFIX)[1].replace(",", "")
        match    = re.search(r"[-+]?\d*\.\d+|\d+", contents)
        return float(match.group()) if match else 0.0


# ── Quick test (modal run pricer_modal.py) ────────────────────────────────────
@app.local_entrypoint()
def main():
    pricer = Pricer()
    test   = "Sony WH-1000XM5 Wireless Noise Cancelling Headphones. 30-hour battery, multipoint connection."
    result = pricer.price.remote(test)
    print(f"Test estimate: ${result:.2f}")
