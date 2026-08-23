import modal
from modal import Volume, Image

app = modal.App("salary-service")
image = Image.debian_slim().pip_install(
    "huggingface", "torch", "transformers", "bitsandbytes", "accelerate", "peft"
)

secrets = [modal.Secret.from_name("huggingface-secret")]

GPU = "T4"
BASE_MODEL = "meta-llama/Llama-3.2-3B"
PROJECT_NAME = "salary"

# ===== CONFIGURE THESE WITH YOUR VALUES FROM WEEK 7 =====
HF_USER = "Joecruise"
RUN_NAME = "2026-03-10_00.18.49-lite"            # e.g. "2025-12-01_14.30.00"
REVISION = "e13d6d61940f9e32439873720c8848ef76a7e0ef"       # commit hash from HF Hub
# =========================================================

PROJECT_RUN_NAME = f"{PROJECT_NAME}-{RUN_NAME}"
FINETUNED_MODEL = f"{HF_USER}/{PROJECT_RUN_NAME}"
CACHE_DIR = "/cache"

MIN_CONTAINERS = 0

PREFIX = "Salary is $"
QUESTION = "What is the annual salary for this position to the nearest thousand dollars?"

hf_cache_volume = Volume.from_name("hf-hub-cache", create_if_missing=True)


@app.cls(
    image=image.env({"HF_HUB_CACHE": CACHE_DIR}),
    secrets=secrets,
    gpu=GPU,
    timeout=1800,
    min_containers=MIN_CONTAINERS,
    volumes={CACHE_DIR: hf_cache_volume},
)
class SalaryPredictor:
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
        self.base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL, quantization_config=quant_config, device_map="auto"
        )
        self.fine_tuned_model = PeftModel.from_pretrained(
            self.base_model, FINETUNED_MODEL, revision=REVISION
        )

    @modal.method()
    def estimate(self, description: str) -> float:
        import re
        import torch
        from transformers import set_seed

        set_seed(42)
        prompt = f"{QUESTION}\n\n{description}\n\n{PREFIX}"

        inputs = self.tokenizer.encode(prompt, return_tensors="pt").to("cuda")
        with torch.no_grad():
            outputs = self.fine_tuned_model.generate(inputs, max_new_tokens=5)
        result = self.tokenizer.decode(outputs[0])
        contents = result.split(PREFIX)[1]
        contents = contents.replace(",", "")
        match = re.search(r"[-+]?\d*\.?\d+", contents)
        return float(match.group()) if match else 0
