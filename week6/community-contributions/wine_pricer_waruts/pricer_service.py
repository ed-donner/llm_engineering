import modal
from modal import Volume, Image

# Setup - define our infrastructure with code!

app = modal.App("wine-pricer-service")
image = Image.debian_slim().pip_install(
    "torch", "transformers==5.18.0", "peft==0.21.2", "bitsandbytes", "accelerate", "huggingface_hub"
)

# This collects the secret from Modal. It must be named "huggingface-secret" in the Modal dashboard
secrets = [modal.Secret.from_name("huggingface-secret")]

GPU = "T4"
BASE_MODEL = "Qwen/Qwen3-4B-Base"
PROJECT_NAME = "wine-pricer"
HF_USER = "Warumanu"
RUN_NAME = "2026-10-05_14.20.52"
PROJECT_RUN_NAME = f"{PROJECT_NAME}-{RUN_NAME}"
FINETUNED_MODEL = f"{HF_USER}/{PROJECT_RUN_NAME}"
CACHE_DIR = "/cache"

# Change this to 1 if you want Modal to be always running, otherwise it will go cold after 2 mins
MIN_CONTAINERS = 0

PREFIX = "Price is $"
QUESTION = "What does this bottle of wine cost to the nearest dollar?"

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
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        from peft import PeftModel

        # Quant Config - the same 4-bit loading as in the Colab notebooks
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
        )

        # Load model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        self.base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            quantization_config=quant_config,
            device_map="auto",
            dtype=torch.float16,
        )
        self.base_model.generation_config.pad_token_id = self.tokenizer.pad_token_id
        self.fine_tuned_model = PeftModel.from_pretrained(self.base_model, FINETUNED_MODEL)
        self.fine_tuned_model.eval()

    @modal.method()
    def price(self, description: str) -> float:
        import re
        import torch
        from transformers import set_seed

        set_seed(42)
        prompt = f"{QUESTION}\n\n{description}\n\n{PREFIX}"

        inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
        with torch.no_grad():
            output_ids = self.fine_tuned_model.generate(**inputs, max_new_tokens=8)
        prompt_length = inputs["input_ids"].shape[1]
        contents = self.tokenizer.decode(output_ids[0, prompt_length:], skip_special_tokens=True)
        contents = contents.replace("$", "").replace(",", "")
        match = re.search(r"[-+]?\d*\.\d+|\d+", contents)
        return float(match.group()) if match else 0
