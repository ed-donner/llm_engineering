import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import httpx
import pandas as pd
import joblib

app = FastAPI(title="Ensemble Agent Service", version="1.0.0")

class PriceRequest(BaseModel):
    description: str

class PriceResponse(BaseModel):
    price: float

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ensemble-agent"}

@app.post("/price", response_model=PriceResponse)
async def estimate_price(request: PriceRequest):
    try:
        prices = []
        errors = []
        
        async with httpx.AsyncClient() as client:
            try:
                specialist_resp = await client.post("http://localhost:8002/price", json={"description": request.description}, timeout=10)
                if specialist_resp.status_code == 200:
                    specialist_data = specialist_resp.json()
                    specialist = specialist_data.get("price", 0.0)
                    prices.append(specialist)
                    logging.info(f"Specialist agent price: ${specialist:.2f}")
                else:
                    errors.append(f"Specialist agent returned status {specialist_resp.status_code}")
            except Exception as e:
                errors.append(f"Specialist agent error: {str(e)}")
            
            try:
                frontier_resp = await client.post("http://localhost:8003/price", json={"description": request.description}, timeout=10)
                if frontier_resp.status_code == 200:
                    frontier_data = frontier_resp.json()
                    frontier = frontier_data.get("price", 0.0)
                    prices.append(frontier)
                    logging.info(f"Frontier agent price: ${frontier:.2f}")
                else:
                    errors.append(f"Frontier agent returned status {frontier_resp.status_code}")
            except Exception as e:
                errors.append(f"Frontier agent error: {str(e)}")
            
            try:
                rf_resp = await client.post("http://localhost:8004/price", json={"description": request.description}, timeout=10)
                if rf_resp.status_code == 200:
                    rf_data = rf_resp.json()
                    random_forest = rf_data.get("price", 0.0)
                    prices.append(random_forest)
                    logging.info(f"Random forest agent price: ${random_forest:.2f}")
                else:
                    errors.append(f"Random forest agent returned status {rf_resp.status_code}")
            except Exception as e:
                errors.append(f"Random forest agent error: {str(e)}")
        
        valid_prices = [p for p in prices if 0 < p < 10000]
        
        if valid_prices:
            y = sum(valid_prices) / len(valid_prices)
            logging.info(f"Ensemble price (from {len(valid_prices)} agents): ${y:.2f}")
        else:
            y = 100.0
            logging.warning(f"No valid prices received, using fallback: ${y:.2f}")
            logging.warning(f"Errors: {errors}")
                
        return PriceResponse(price=y)
    except Exception as e:
        logging.error(f"Error in estimate_price: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
