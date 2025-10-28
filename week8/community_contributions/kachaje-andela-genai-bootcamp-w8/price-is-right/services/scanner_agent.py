import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import ollama
import logging
from shared.services.scanner_wrapper import ScannerAgentWrapper

app = FastAPI(title="Scanner Agent Service", version="1.0.0")

scanner_agent = ScannerAgentWrapper()

class MemoryRequest(BaseModel):
    memory: List[str] = []

class DealSelectionResponse(BaseModel):
    deals: List[dict]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "scanner-agent"}

@app.post("/scan", response_model=DealSelectionResponse)
async def scan_deals(request: MemoryRequest):
    try:
        result = scanner_agent.scan(request.memory)
        if result:
            return DealSelectionResponse(deals=[deal.model_dump() for deal in result.deals])
        else:
            return DealSelectionResponse(deals=[])
    except Exception as e:
        logging.error(f"Error in scan_deals: {str(e)}")
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
    
    port = 8001
    if not is_port_available(port):
        logging.warning(f"Port {port} is already in use. Trying alternative ports...")
        for alt_port in range(8001, 8010):
            if is_port_available(alt_port):
                port = alt_port
                logging.info(f"Using alternative port: {port}")
                break
        else:
            logging.error("No available ports found in range 8001-8009")
            sys.exit(1)
    
    logging.info(f"Starting Scanner Agent service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
