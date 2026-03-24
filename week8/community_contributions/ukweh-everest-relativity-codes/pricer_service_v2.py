import modal
from fastapi import FastAPI
from pydantic import BaseModel
import os

# 1. Define Infrastructure
app = modal.App("deal-hunter-production")
image = modal.Image.debian_slim().pip_install(
    "torch", "transformers", "bitsandbytes", "accelerate", "peft", "fastapi"
)

web_app = FastAPI()

# 2. Pydantic Models for API
class PriceRequest(BaseModel):
    description: str

class PriceResponse(BaseModel):
    estimate: float
    status: str

# 3. Model Inference (Runs on GPU in Cloud)
@app.function(
    image=image, 
    gpu="T4", 
    secrets=[modal.Secret.from_name("huggingface-secret")],
    timeout=600
)
def get_prediction(description: str) -> float:
    # This is where your Week 7 Fine-tuned model logic goes
    # For demo, returns a mock value
    return 99.99

# 4. API Endpoints
@web_app.post("/predict", response_model=PriceResponse)
async def predict_endpoint(request: PriceRequest):
    try:
        price = get_prediction.remote(request.description)
        return PriceResponse(estimate=price, status="success")
    except Exception as e:
        return PriceResponse(estimate=0.0, status=f"error: {str(e)}")

# 5. Modal Entrypoint
@app.function()
@modal.asgi_app()
def api():
    return web_app
