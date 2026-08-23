import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import gradio as gr
import httpx
import logging
import asyncio
import socket

app = FastAPI(title="Notification Receiver", version="1.0.0")

notifications = []

class NotificationRequest(BaseModel):
    message: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "notification-receiver"}

@app.post("/notification")
async def receive_notification(request: NotificationRequest):
    notifications.append(request.message)
    return {"status": "received"}

def get_notifications():
    return "\n".join(notifications[-10:])

def find_available_port(start_port: int, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No available port found in range {start_port}-{start_port + max_attempts - 1}")

def create_gradio_interface():
    with gr.Blocks(title="Deal Notifications") as interface:
        gr.Markdown("# Deal Notifications")
        output = gr.Textbox(label="Recent Notifications", lines=10, interactive=False)
        
        def update():
            return get_notifications()
        
        interface.load(update, outputs=output)
        gr.Timer(value=5).tick(update, outputs=output)
    
    return interface

if __name__ == "__main__":
    import uvicorn
    import threading
    import signal
    
    # Find available ports
    try:
        fastapi_port = find_available_port(8008)
        gradio_port = find_available_port(7861)
        print(f"Using FastAPI port: {fastapi_port}")
        print(f"Using Gradio port: {gradio_port}")
    except RuntimeError as e:
        print(f"Failed to find available ports: {e}")
        sys.exit(1)
    
    async def subscribe_to_notifications():
        try:
            async with httpx.AsyncClient() as client:
                await client.post("http://localhost:8007/subscribe", json={"url": f"http://localhost:{fastapi_port}"})
                print(f"Successfully subscribed to notifications on port {fastapi_port}")
        except Exception as e:
            print(f"Failed to subscribe to notifications: {e}")
    
    def run_fastapi():
        try:
            uvicorn.run(app, host="0.0.0.0", port=fastapi_port)
        except Exception as e:
            print(f"FastAPI server error: {e}")
    
    def signal_handler(signum, frame):
        print("\nReceived interrupt signal. Shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start FastAPI server in background thread
        fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
        fastapi_thread.start()
        
        # Start subscription in background thread
        subscription_thread = threading.Thread(target=lambda: asyncio.run(subscribe_to_notifications()), daemon=True)
        subscription_thread.start()
        
        # Give services time to start
        import time
        time.sleep(2)
        
        # Start Gradio interface
        interface = create_gradio_interface()
        interface.launch(server_name="0.0.0.0", server_port=gradio_port, share=False)
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error starting services: {e}")
        sys.exit(1)
