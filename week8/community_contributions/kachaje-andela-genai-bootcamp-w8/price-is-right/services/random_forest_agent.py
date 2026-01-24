import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Random Forest Agent Service", version="1.0.0")

try:
    logger.info("Initializing Random Forest Agent...")
    from shared.services.random_forest_wrapper import RandomForestAgentWrapper
    random_forest_agent = RandomForestAgentWrapper()
    logger.info("Random Forest Agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Random Forest Agent: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    random_forest_agent = None

class PriceRequest(BaseModel):
    description: str

class PriceResponse(BaseModel):
    price: float

@app.get("/health")
async def health_check():
    if random_forest_agent is None:
        return {"status": "unhealthy", "service": "random-forest-agent", "error": "Agent not initialized"}
    return {"status": "healthy", "service": "random-forest-agent"}

@app.post("/price", response_model=PriceResponse)
async def estimate_price(request: PriceRequest):
    try:
        if random_forest_agent is None:
            logger.error("Random Forest Agent not initialized")
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        logger.info(f"Processing price request for: {request.description}")
        price = random_forest_agent.price(request.description)
        logger.info(f"Price estimate: ${price:.2f}")
        return PriceResponse(price=price)
    except Exception as e:
        logger.error(f"Error in estimate_price: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import socket
    
    def is_port_available(port):
        """Check if a port is available"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return True
            except OSError:
                return False
    
    port = 8004
    if not is_port_available(port):
        logger.warning(f"Port {port} is already in use. Trying alternative ports...")
        for alt_port in range(8004, 8010):
            if is_port_available(alt_port):
                port = alt_port
                logger.info(f"Using alternative port: {port}")
                break
        else:
            logger.error("No available ports found in range 8004-8009")
            sys.exit(1)
    
    logger.info(f"Starting Random Forest Agent service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
