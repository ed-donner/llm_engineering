# LoRA + base model pricer on Modal with Gradio
import modal
from modal import Image

BASE_MODEL = "unsloth/Qwen2.5-Math-1.5B-bnb-4bit"
ADAPTER_REPO = "martinsawojide/price-2026-03-06_17.59.28"
ADAPTER_REVISION = None
GPU = "T4"
HF_SECRET_NAME = "huggingface-secret"
PUSHOVER_SECRET_NAME = "pushover-secret"
MIN_CONTAINERS = 0
SCALEDOWN_WINDOW = 300

app = modal.App("lora-gradio-pricer")
image = (
    Image.debian_slim()
    .pip_install("torch", "transformers", "peft", "accelerate", "bitsandbytes", "requests", "gradio")
    .env({
        "BASE_MODEL": BASE_MODEL,
        "ADAPTER_REPO": ADAPTER_REPO,
        "ADAPTER_REVISION": str(ADAPTER_REVISION) if ADAPTER_REVISION else "",
    })
)
secrets = [modal.Secret.from_name(HF_SECRET_NAME)]
if PUSHOVER_SECRET_NAME:
    secrets.append(modal.Secret.from_name(PUSHOVER_SECRET_NAME))

PREFIX = "Price is $"
QUESTION = "What does this cost to the nearest dollar?"


@app.cls(
    image=image,
    secrets=secrets,
    gpu=GPU,
    timeout=600,
    min_containers=MIN_CONTAINERS,
    scaledown_window=SCALEDOWN_WINDOW,
    # region="eu",
)

class Pricer:
    @modal.enter()
    def setup(self):
        import logging
        import os
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, set_seed
        from peft import PeftModel

        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self._log = logging.getLogger("pricer")

        base_id = os.environ["BASE_MODEL"]
        adapter_id = os.environ["ADAPTER_REPO"]
        revision = os.environ.get("ADAPTER_REVISION") or None

        self._log.info("Loading tokenizer and base model: %s", base_id)
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
        )
        self.tokenizer = AutoTokenizer.from_pretrained(base_id)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        base_model = AutoModelForCausalLM.from_pretrained(
            base_id, quantization_config=quant_config, device_map="auto"
        )
        self._log.info("Loading LoRA adapter: %s", adapter_id)
        self.model = PeftModel.from_pretrained(base_model, adapter_id, revision=revision)
        self.prefix = os.environ.get("PREFIX", "Price is $")
        self.question = os.environ.get("QUESTION", "What does this cost to the nearest dollar?")
        self._log.info("Setup complete — model ready")

    @modal.method()
    def price(self, description: str) -> float:
        import os
        import re
        import torch
        import requests
        from transformers import set_seed

        self._log.info("price request: %s", (description[:80] + "..." if len(description) > 80 else description))
        set_seed(42)
        prompt = f"{self.question}\n\n{description}\n\n{self.prefix}"
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=8)
        text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        if self.prefix not in text:
            price = 0.0
        else:
            contents = text.split(self.prefix)[1].replace(",", "")
            match = re.search(r"[-+]?\d*\.\d+|\d+", contents)
            price = float(match.group()) if match else 0.0

        self._log.info("inference done: price=%.2f", price)

        msg_body = f"Estimated price: ${price:.2f}\n\nProduct: {description[:500]}"

        token = os.environ.get("PUSHOVER_TOKEN")
        user = os.environ.get("PUSHOVER_USER")
        if token and user:
            try:
                requests.post(
                    "https://api.pushover.net/1/messages",
                    data={
                        "token": token,
                        "user": user,
                        "message": msg_body,
                        "title": "Pricer",
                    },
                    timeout=10,
                )
                self._log.info("Pushover notification sent")
            except Exception as e:
                self._log.warning("Pushover failed: %s", e)
        else:
            self._log.debug("Pushover skipped (no secret)")

        return price

@app.local_entrypoint()
def main():

    import gradio as gr

    def ui_predict(description: str) -> str:
        if not description.strip():
            return "Enter a product description."
        raw = Pricer().price.remote(description)
        price = raw.get() if hasattr(raw, "get") else raw
        return f"Estimated price: ${price:.2f}"


    EXAMPLE_DESCRIPTION = """Title: Schlage F59 & 613 Andover Interior Knob (Deadbolt Included)
Category: Home Hardware
Brand: Schlage
Description: A single-piece oil-rubbed bronze knob that mounts to a deadbolt for secure, easy interior door use.
Details: Designed for a 4" minimum center-to-center door prep, it offers a lifetime mechanical and finish warranty and comes ready for quick installation."""

    with gr.Blocks(title="Pricer — LoRA + Base (Modal)") as demo:
        gr.Markdown("## Price estimator (inference on Modal)")
        gr.Markdown("Enter a product description to get an estimated price (nearest dollar).")
        inp = gr.Textbox(
            label="Product description",
            placeholder="e.g. USB-C laptop charger 65W",
            lines=3,
        )
        out = gr.Textbox(label="Result")
        inp.submit(ui_predict, inputs=inp, outputs=out)
        gr.Button("Get price").click(ui_predict, inputs=inp, outputs=out)
        gr.Examples(
            examples=[[EXAMPLE_DESCRIPTION]],
            inputs=inp,
            label="Example: Schlage interior knob (deadbolt), Home Hardware",
        )

    demo.launch()
