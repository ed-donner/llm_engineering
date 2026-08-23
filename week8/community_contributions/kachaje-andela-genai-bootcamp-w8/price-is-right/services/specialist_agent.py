import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Specialist Agent Service", version="1.0.0")

try:
    logger.info("Initializing Specialist Agent...")
    from shared.services.specialist_wrapper import SpecialistAgentWrapper
    specialist_agent = SpecialistAgentWrapper()
    logger.info("Specialist Agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Specialist Agent: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    specialist_agent = None

class PriceRequest(BaseModel):
    description: str

class PriceResponse(BaseModel):
    price: float

@app.get("/health")
async def health_check():
    if specialist_agent is None:
        return {"status": "unhealthy", "service": "specialist-agent", "error": "Agent not initialized"}
    return {"status": "healthy", "service": "specialist-agent"}

@app.post("/price", response_model=PriceResponse)
async def estimate_price(request: PriceRequest):
    try:
        if specialist_agent is None:
            logger.error("Specialist Agent not initialized")
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        logger.info(f"Processing price request for: {request.description}")
        price = specialist_agent.price(request.description)
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
    
    port = 8002
    if not is_port_available(port):
        logger.warning(f"Port {port} is already in use. Trying alternative ports...")
        for alt_port in range(8002, 8010):
            if is_port_available(alt_port):
                port = alt_port
                logger.info(f"Using alternative port: {port}")
                break
        else:
            logger.error("No available ports found in range 8002-8009")
            sys.exit(1)
    
    logger.info(f"Starting Specialist Agent service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
