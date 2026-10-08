import os

from dotenv import load_dotenv
from huggingface_hub import InferenceClient


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# HUGGING FACE TOKEN
# ============================================================

HF_TOKEN = os.getenv("HF_TOKEN")


if not HF_TOKEN:
    raise ValueError(
        "HF_TOKEN is not set in .env file."
    )


# ============================================================
# HUGGING FACE CLIENT
# ============================================================

client = InferenceClient(
    api_key=HF_TOKEN
)


# ============================================================
# IMAGE MODEL
# ============================================================

MODEL_ID = "black-forest-labs/FLUX.1-schnell"


# ============================================================
# GENERATE IMAGE
# ============================================================

def generate_image(
    prompt,
    output_path="generated_image.png"
):

    print("Sending image generation request to Hugging Face...")

    try:

        image = client.text_to_image(
            prompt=prompt,
            model=MODEL_ID,
            width=512,
            height=512,
            num_inference_steps=4
        )

        image.save(output_path)

        print(
            f"Image generated successfully: {output_path}"
        )

        return output_path

    except Exception as e:

        raise RuntimeError(
            f"Hugging Face image generation failed: {e}"
        )