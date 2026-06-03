import modal
from modal import App, Volume, Image

# Setup - define our infrastructure with code!

app = modal.App("pricer-service")
image = Image.debian_slim().pip_install("huggingface", "torch", "transformers", "bitsandbytes", "accelerate", "peft")
secrets = [modal.Secret.from_name("hf-secret")]

# Constants

GPU = "T4"
BASE_MODEL = "meta-llama/Meta-Llama-3.1-8B"
PROJECT_NAME = "pricer"
HF_USER = "ed-donner" # your HF name here! Or use mine if you just want to reproduce my results.
RUN_NAME = "2024-09-13_13.04.39"
PROJECT_RUN_NAME = f"{PROJECT_NAME}-{RUN_NAME}"
REVISION = "e8d637df551603dc86cd7a1598a8f44af4d7ae36"
FINETUNED_MODEL = f"{HF_USER}/{PROJECT_RUN_NAME}"
MODEL_DIR = "hf-cache/"
BASE_DIR = MODEL_DIR + BASE_MODEL
FINETUNED_DIR = MODEL_DIR + FINETUNED_MODEL

QUESTION = "How much does this cost to the nearest dollar?"
PREFIX = "Price is $"

@app.cls(image=image, secrets=secrets, gpu=GPU, timeout=1800)
class Pricer:
    @modal.build()
    def download_model_to_folder(self):
        from huggingface_hub import snapshot_download
        import os
        os.makedirs(MODEL_DIR, exist_ok=True)
        snapshot_download(BASE_MODEL, local_dir=BASE_DIR)
        snapshot_download(FINETUNED_MODEL, revision=REVISION, local_dir=FINETUNED_DIR)

    @modal.enter()
    def setup(self):
        import os
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, set_seed
        from peft import PeftModel
        
        # Quant Config
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_type="nf4"
        )
    
        # Load model and tokenizer
        
        self.tokenizer = AutoTokenizer.from_pretrained(BASE_DIR)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        
        self.base_model = AutoModelForCausalLM.from_pretrained(
            BASE_DIR, 
            quantization_config=quant_config,
            device_map="auto"
        )
    
        self.fine_tuned_model = PeftModel.from_pretrained(self.base_model, FINETUNED_DIR, revision=REVISION)

    @modal.method()
    def price(self, description: str) -> float:
        import os
        import re
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, set_seed
        from peft import PeftModel
    
        set_seed(42)
        prompt = f"{QUESTION}\n\n{description}\n\n{PREFIX}"
        inputs = self.tokenizer.encode(prompt, return_tensors="pt").to("cuda")
        attention_mask = torch.ones(inputs.shape, device="cuda")
        outputs = self.fine_tuned_model.generate(inputs, attention_mask=attention_mask, max_new_tokens=5, num_return_sequences=1)
        result = self.tokenizer.decode(outputs[0])
    
        contents = result.split("Price is $")[1]
        contents = contents.replace(',','')
        match = re.search(r"[-+]?\d*\.\d+|\d+", contents)
        return float(match.group()) if match else 0

    @modal.method()
    def wake_up(self) -> str:
        return "ok"

