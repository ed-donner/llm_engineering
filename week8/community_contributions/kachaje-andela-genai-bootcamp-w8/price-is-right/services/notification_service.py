import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import asyncio
import json
import socket
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Notification Service", version="1.0.0")

subscribers = []

class AlertRequest(BaseModel):
    deal: dict
    estimate: float
    discount: float

class SubscriberRequest(BaseModel):
    url: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "notification-service"}

@app.post("/subscribe")
async def subscribe(request: SubscriberRequest):
    subscribers.append(request.url)
    return {"status": "subscribed"}

@app.post("/alert")
async def send_alert(request: AlertRequest):
    message = f"Deal Alert! Price=${request.deal['price']:.2f}, Estimate=${request.estimate:.2f}, Discount=${request.discount:.2f} : {request.deal['product_description'][:10]}... {request.deal['url']}"
    
    logger.info(f"Sending alert to {len(subscribers)} subscribers")
    
    for subscriber in subscribers:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(f"{subscriber}/notification", json={"message": message})
                logger.info(f"Successfully notified {subscriber}")
        except Exception as e:
            logger.error(f"Failed to notify {subscriber}: {e}")
    
    return {"status": "alert_sent"}

def is_port_available(port: int) -> bool:
    """Check if a port is available for binding"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', port))
            return True
    except OSError:
        return False

if __name__ == "__main__":
    import uvicorn
    
    port = 8007
    
    # Check if port is available before starting
    if not is_port_available(port):
        logger.error(f"Port {port} is already in use. Please stop the existing service or use a different port.")
        sys.exit(1)
    
    logger.info(f"Starting Notification Service on port {port}")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        sys.exit(1)
