"""
Modal deployment for the fine-tuned clinical triage Llama 3.2 3B model (from Week 7).

Deploy with:
    uv run modal deploy modal_triage_service.py

Then call from Python:
    import modal
    TriageClassifier = modal.Cls.from_name("clinical-triage-service", "TriageClassifier")
    classifier = TriageClassifier()
    result = classifier.classify.remote("72yo male, crushing chest pain, sweating, BP 80/50")
"""

import os
import modal

APP_NAME = "clinical-triage-service"
# Set this to your HuggingFace model repo from Week 7
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME", "AcharO/clinical-triage-llama")
BASE_MODEL = "meta-llama/Llama-3.2-3B"
TRIAGE_LEVELS = ["Immediate", "Urgent", "Semi-urgent", "Non-urgent"]

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch",
        "transformers",
        "peft",
        "bitsandbytes",
        "accelerate",
        "sentencepiece",
    )
)

app = modal.App(APP_NAME)


@app.cls(
    gpu="T4",
    image=image,
    secrets=[modal.Secret.from_name("huggingface-secret")],
    min_containers=0,  # set to 1 to keep warm (uses credits)
    timeout=120,
)
class TriageClassifier:

    @modal.enter()
    def load_model(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import PeftModel

        print(f"Loading base model: {BASE_MODEL}")
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_type="nf4",
        )
        base = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            quantization_config=quant_config,
            device_map="auto",
        )
        print(f"Loading LoRA adapters: {HF_MODEL_NAME}")
        self.model = PeftModel.from_pretrained(base, HF_MODEL_NAME)
        self.tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_NAME)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        print("Model ready.")

    @modal.method()
    def classify(self, presentation: str) -> str:
        import torch

        system_msg = """You are a clinical triage assistant. Classify the urgency of the patient presentation.
Respond with exactly one word: Immediate, Urgent, Semi-urgent, or Non-urgent."""

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": f"Triage this patient:\n{presentation}"},
        ]
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=10,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        response = self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

        for level in TRIAGE_LEVELS:
            if level.lower() in response.lower():
                return level
        return "Unknown"
