import modal
from modal import Volume, Image
import torch

# --- Modal App & Image ---
app = modal.App("shopping-advisor")
image = Image.debian_slim().pip_install(
    "huggingface", "torch", "transformers", "bitsandbytes", "accelerate", "peft"
)

# --- Secrets ---
secrets = [modal.Secret.from_name("huggingface-secret")]

# --- GPU & Model Config ---
GPU = "T4"
PRICE_MODEL = "ojov/price-2026-03-09_07.17.58-lite"
REASON_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
CACHE_DIR = "/cache"

# Cache volume
hf_cache_volume = Volume.from_name("hf-hub-cache", create_if_missing=True)

# --- Modal Class ---
@app.cls(
    image=image.env({"HF_HUB_CACHE": CACHE_DIR}),
    secrets=secrets,
    gpu=GPU,
    timeout=1800,
    min_containers=1,
    volumes={CACHE_DIR: hf_cache_volume},
)
class ShoppingAdvisor:

    @modal.enter()
    def setup(self):
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM

        # --- Load price model ---
        self.price_tokenizer = AutoTokenizer.from_pretrained(PRICE_MODEL, cache_dir=CACHE_DIR)
        self.price_model = AutoModelForCausalLM.from_pretrained(
            PRICE_MODEL, device_map="auto", cache_dir=CACHE_DIR
        )

        # --- Load reasoning model ---
        self.reason_tokenizer = AutoTokenizer.from_pretrained(REASON_MODEL, cache_dir=CACHE_DIR)
        self.reason_model = AutoModelForCausalLM.from_pretrained(
            REASON_MODEL, device_map="auto", cache_dir=CACHE_DIR
        )

    def estimate_price(self, description: str) -> float:
        import torch
        import re

        prompt = f"""What does this cost to the nearest dollar?\n\nTitle: {description}\n\nPrice is $"""
        inputs = self.price_tokenizer(prompt, return_tensors="pt").to("cuda")
        with torch.no_grad():
            outputs = self.price_model.generate(**inputs, max_new_tokens=6)
        text = self.price_tokenizer.decode(outputs[0])
        try:
            return float(re.search(r"[-+]?\d*\.\d+|\d+", text.split("$")[-1]).group())
        except:
            return None
        


    def generate_reason(self, description, estimate, price, verdict):

        prompt = f"Product: {description}\nEstimated fair price: ${estimate}\nActual price: ${price}\nVerdict: {verdict}\nOne sentence explanation:"

        inputs = self.reason_tokenizer(prompt, return_tensors="pt").to("cuda")
        input_length = inputs["input_ids"].shape[1]

        with torch.no_grad():
            output = self.reason_model.generate(
                **inputs,
                max_new_tokens=40,
                eos_token_id=self.reason_tokenizer.eos_token_id,
                pad_token_id=self.reason_tokenizer.eos_token_id,
            )

        new_tokens = output[0][input_length:]
        result = self.reason_tokenizer.decode(new_tokens, skip_special_tokens=True)
        
        # Take only the first sentence
        first_sentence = result.split("\n")[0].strip()
        return first_sentence

    # --- Evaluate a deal ---
    @modal.method()
    def evaluate(self, description: str, price: float):
        estimate = self.estimate_price(description)
        if estimate is None:
            return {"error": "Could not estimate price"}

        diff = estimate - price
        if diff > 80:
            verdict = "Excellent deal"
        elif diff > 30:
            verdict = "Good deal"
        elif diff > -20:
            verdict = "Fair price"
        else:
            verdict = "Overpriced"

        explanation = self.generate_reason(description, estimate, price, verdict)

        return {
            "product": description,
            "estimated_price": estimate,
            "actual_price": price,
            "difference": diff,
            "recommendation": verdict,
            "reason": explanation
        }