import modal

app = modal.App("wakanda-pricer-service")
image = (
    modal.Image.debian_slim()
    .pip_install("torch", "transformers", "bitsandbytes", "accelerate", "peft", "huggingface_hub")
    .env({"HF_HUB_CACHE": "/cache"})
)

BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
HF_MODEL_NAME_ENV = "chimaken/pricer-ft-qlora"
PRICE_PROMPT = "Estimate the price in USD. Reply with only the number."
PREFIX = "Price is $"
MAX_SEQ_LENGTH = 512
GPU = "T4"
CACHE_PATH = "/cache"
cache_vol = modal.Volume.from_name("wakanda-hf-cache", create_if_missing=True)
secrets = [modal.Secret.from_name("huggingface-secret")]


@app.cls(
    image=image,
    secrets=secrets,
    volumes={CACHE_PATH: cache_vol},
    gpu=GPU,
    timeout=600,
    region="us-east",
)
class SpecialistPricer:
    @modal.enter()
    def setup(self):
        import os
        import re
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        from peft import PeftModel
        from huggingface_hub import snapshot_download

        os.makedirs(CACHE_PATH, exist_ok=True)
        hf_model = os.environ.get(HF_MODEL_NAME_ENV, "").strip() or os.environ.get("HF_USER", "chimaken") + "/pricer-ft-qlora"

        snapshot_download(BASE_MODEL, local_dir=f"{CACHE_PATH}/base")
        snapshot_download(hf_model, local_dir=f"{CACHE_PATH}/ft")

        bnb = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype="float16",
            bnb_4bit_quant_type="nf4",
        )
        self.tokenizer = AutoTokenizer.from_pretrained(f"{CACHE_PATH}/base")
        self.tokenizer.pad_token = self.tokenizer.eos_token
        base = AutoModelForCausalLM.from_pretrained(
            f"{CACHE_PATH}/base",
            quantization_config=bnb,
            device_map="auto",
        )
        self.model = PeftModel.from_pretrained(base, f"{CACHE_PATH}/ft")
        self.model.eval()
        self._re = re

    @modal.method()
    def price(self, description: str) -> float:
        import torch
        text = (description or "").strip()[:1200]
        prompt = f"{PRICE_PROMPT}\n\n{text}\n\n{PREFIX}"
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_SEQ_LENGTH,
        ).to(self.model.device)
        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=16,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        reply = self.tokenizer.decode(
            out[0][inputs["input_ids"].shape[1] :],
            skip_special_tokens=True,
        ).strip()
        s = reply.replace("$", "").replace(",", "")
        m = self._re.search(r"[-+]?\d*\.?\d+", s)
        return max(0.0, float(m.group())) if m else 0.0
