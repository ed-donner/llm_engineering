import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
import httpx
import json

app = FastAPI(title="Planning Agent Service", version="1.0.0")

class MemoryRequest(BaseModel):
    memory: List[str] = []

class OpportunityResponse(BaseModel):
    deal: dict
    estimate: float
    discount: float

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "planning-agent"}

@app.post("/plan", response_model=Optional[OpportunityResponse])
async def plan_deals(request: MemoryRequest):
    try:
        async with httpx.AsyncClient() as client:
            try:
                scanner_resp = await client.post("http://localhost:8001/scan", json={"memory": request.memory}, timeout=30)
                scanner_data = scanner_resp.json()
            except Exception as e:
                logging.error(f"Error calling scanner agent: {str(e)}")
                return None
            
            if not scanner_data.get("deals"):
                logging.info("No deals found by scanner agent")
                return None
                
            best_deal = None
            best_discount = 0
            
            for deal in scanner_data["deals"][:5]:
                try:
                    ensemble_resp = await client.post("http://localhost:8005/price", json={"description": deal["product_description"]}, timeout=30)
                    estimate = ensemble_resp.json()["price"]
                    discount = estimate - deal["price"]
                    
                    if discount > best_discount:
                        best_discount = discount
                        best_deal = {
                            "deal": deal,
                            "estimate": estimate,
                            "discount": discount
                        }
                except Exception as e:
                    logging.error(f"Error calling ensemble agent for deal {deal.get('product_description', 'unknown')}: {str(e)}")
                    continue
            
            if best_discount > 50:
                try:
                    await client.post("http://localhost:8007/alert", json=best_deal, timeout=10)
                    logging.info(f"Sent notification for deal with ${best_discount:.2f} discount")
                except Exception as e:
                    logging.error(f"Error sending notification: {str(e)}")
                
                return OpportunityResponse(**best_deal)
            
            logging.info(f"Best deal discount ${best_discount:.2f} is not significant enough")
            return None
            
    except Exception as e:
        logging.error(f"Error in plan_deals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
