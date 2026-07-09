import modal
from modal import Image

# Setup

app = modal.App("llama")
image = Image.debian_slim().pip_install("torch", "transformers", "accelerate")
secrets = [modal.Secret.from_name("huggingface-secret")]
GPU = "T4"
MODEL_NAME = "meta-llama/Llama-3.2-3B"


@app.function(image=image, secrets=secrets, gpu=GPU, timeout=1800)
def generate(prompt: str) -> str:
    from transformers import AutoTokenizer, AutoModelForCausalLM, set_seed

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, device_map="auto")

    set_seed(42)
    inputs = tokenizer.encode(prompt, return_tensors="pt").to("cuda")
    outputs = model.generate(inputs, max_new_tokens=5)
    return tokenizer.decode(outputs[0])
