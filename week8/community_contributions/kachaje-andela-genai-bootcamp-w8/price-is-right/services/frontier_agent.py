import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from shared.services.frontier_wrapper import FrontierAgentWrapper

app = FastAPI(title="Frontier Agent Service", version="1.0.0")

frontier_agent = FrontierAgentWrapper()

class PriceRequest(BaseModel):
    description: str

class PriceResponse(BaseModel):
    price: float

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "frontier-agent"}

@app.post("/price", response_model=PriceResponse)
async def estimate_price(request: PriceRequest):
    try:
        price = frontier_agent.price(request.description)
        return PriceResponse(price=price)
    except Exception as e:
        logging.error(f"Error in estimate_price: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
