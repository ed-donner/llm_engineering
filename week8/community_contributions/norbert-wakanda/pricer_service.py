"""
Modal-hosted Llama pricing service for the week8-project.

Deploy with:
    modal deploy pricer_service.py

This runs your fine-tuned Llama-3.2-3B model on a GPU in Modal's cloud.
The model loads once on container start (@modal.enter) and stays warm
for subsequent calls, making repeated price() calls fast.
"""

# modal deploy -m pricer_service

import modal
from modal import Image, Volume

# ---------------------------------------------------------------------------
# Infrastructure definition
# ---------------------------------------------------------------------------

app = modal.App("week8-project-pricer")

image = Image.debian_slim().pip_install(
    "torch", "transformers", "bitsandbytes", "accelerate", "peft"
)

secrets = [modal.Secret.from_name("huggingface-secret")]

# Persistent volume caches the downloaded model weights across cold starts
hf_cache_volume = Volume.from_name("hf-hub-cache", create_if_missing=True)

# ---------------------------------------------------------------------------
# Constants — update HF_USER to your own HuggingFace username
# ---------------------------------------------------------------------------

GPU = "T4"
CACHE_DIR = "/cache"
BASE_MODEL = "meta-llama/Llama-3.2-3B"

HF_USER = "mainanorbert"
PROJECT_NAME = "price"
RUN_NAME = "2026-03-04_08.48.39"
FINETUNED_MODEL = f"{HF_USER}/{PROJECT_NAME}-{RUN_NAME}-lite"
REVISION = "main"

PREFIX = "Price is $"
QUESTION = "What does this cost to the nearest dollar?"

# Set to 1 to keep the container always warm (faster, but costs more)
MIN_CONTAINERS = 0


# ---------------------------------------------------------------------------
# Pricer class — runs remotely on Modal GPU
# ---------------------------------------------------------------------------

@app.cls(
    image=image.env({"HF_HUB_CACHE": CACHE_DIR}),
    secrets=secrets,
    gpu=GPU,
    timeout=1800,
    min_containers=MIN_CONTAINERS,
    volumes={CACHE_DIR: hf_cache_volume},
)
class Pricer:
    """
    A Modal class that loads a fine-tuned Llama model once and exposes
    a price() method for fast repeated inference.

    The model is loaded in @modal.enter so it stays in memory across
    multiple calls to the same container — no cold-load penalty per request.
    """

    @modal.enter()
    def setup(self):
        """Load the tokenizer and fine-tuned model into GPU memory."""
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
        self.model = PeftModel.from_pretrained(base_model, FINETUNED_MODEL, revision=REVISION)

    @modal.method()
    def price(self, description: str) -> float:
        """
        Estimate the USD price of a product from its description.

        Args:
            description: Plain-text product description or title.

        Returns:
            Estimated price as a float (e.g. 78.0). Returns 0.0 if the
            model output cannot be parsed as a number.
        """
        import re
        import torch
        from transformers import set_seed

        set_seed(42)
        prompt = f"{QUESTION}\n\n{description}\n\n{PREFIX}"

        inputs = self.tokenizer.encode(prompt, return_tensors="pt").to("cuda")
        with torch.no_grad():
            outputs = self.model.generate(inputs, max_new_tokens=5)

        decoded = self.tokenizer.decode(outputs[0])
        after_prefix = decoded.split(PREFIX)[-1].replace(",", "")
        match = re.search(r"[-+]?\d*\.\d+|\d+", after_prefix)
        return float(match.group()) if match else 0.0
