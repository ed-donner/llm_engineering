"""
Real-Time API Gateway (FastAPI + WebSocket)

WebSocket endpoint for receiving audio chunks from frontend and pushing to Redis Stream.
"""

import os
import json
import base64
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from redis_client import redis_client, RedisStreamClient
from models import AudioChunkRequest, ControlMessage, StatusResponse, WebSocketMessage
from utils.retry import retry_with_backoff
from utils.audio_storage import audio_storage
import redis as redis_lib

# Load .env from project root
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    logger.info("🚀 Starting API Gateway...")
    
    # Test Redis connection
    if redis_client.ping():
        logger.info("✅ Redis connection established")
    else:
        logger.warning("⚠️  Redis connection failed - audio chunks will not be queued")
    
    logger.info("✨ API Gateway ready")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down API Gateway...")
    redis_client.close()
    logger.info("✅ Shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    lifespan=lifespan,
    title="Real-Time Call Center AI API Gateway",
    description="WebSocket API for live audio transcription and processing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}
active_sessions: Dict[str, dict] = {}  # call_id -> session info


def validate_session(call_id: str, agent_id: str) -> bool:
    """
    Validate session credentials.
    
    Args:
        call_id: Call identifier
        agent_id: Agent identifier
        
    Returns:
        True if valid, False otherwise
    """
    # Basic validation - in production, add proper authentication
    if not call_id or not agent_id:
        return False
    
    # Check if call_id is a valid UUID format
    try:
        import uuid
        uuid.UUID(call_id)
    except ValueError:
        return False
    
    return True


def preprocess_audio_chunk(
    audio_data: bytes,
    format: str = "pcm",
    sample_rate: int = 16000,
    channels: int = 1
) -> dict:
    """
    Preprocess audio chunk with metadata.
    
    Args:
        audio_data: Raw audio bytes
        format: Audio format
        sample_rate: Sample rate in Hz
        channels: Number of channels
        
    Returns:
        Dictionary with preprocessing metadata
    """
    return {
        'format': format,
        'sample_rate': sample_rate,
        'channels': channels,
        'size_bytes': len(audio_data),
        'duration_estimate': len(audio_data) / (sample_rate * channels * 2),  # Rough estimate for 16-bit PCM
        'processed_at': datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Real-Time Call Center AI API Gateway",
        "version": "1.0.0",
        "redis_connected": redis_client.ping()
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    redis_status = redis_client.ping()
    stream_info = redis_client.get_stream_info() if redis_status else {}
    
    return {
        "status": "healthy" if redis_status else "degraded",
        "redis": {
            "connected": redis_status,
            "stream_info": stream_info
        },
        "active_connections": len(active_connections),
        "active_sessions": len(active_sessions)
    }


@app.websocket("/ws/call")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio ingestion.
    
    Receives audio chunks from frontend and pushes them to Redis Stream.
    """
    await websocket.accept()
    logger.info("New WebSocket connection established")
    
    call_id = None
    agent_id = None
    chunk_count = 0
    
    try:
        # Wait for initial session setup message
        try:
            initial_message = await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info("Client disconnected before sending initial message")
            return
        except Exception as e:
            logger.error(f"Error receiving initial message: {e}")
            return
        
        try:
            data = json.loads(initial_message)
            call_id = data.get('call_id')
            agent_id = data.get('agent_id')
            action = data.get('action', 'start')
            
            # Validate session
            if not validate_session(call_id, agent_id):
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid session credentials"
                })
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            
            # Store session
            session_key = f"{call_id}:{agent_id}"
            active_connections[session_key] = websocket
            active_sessions[call_id] = {
                'call_id': call_id,
                'agent_id': agent_id,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            logger.info(f"Session started: call_id={call_id}, agent_id={agent_id}")
            
            # Send confirmation
            await websocket.send_json({
                "type": "session_started",
                "call_id": call_id,
                "agent_id": agent_id,
                "message": "Session established. Ready to receive audio chunks."
            })
            
        except json.JSONDecodeError:
            await websocket.send_json({
                "type": "error",
                "message": "Invalid JSON in initial message"
            })
            await websocket.close()
            return
        
        # Main loop: receive audio chunks
        while True:
            try:
                # Check if WebSocket is still connected before receiving
                if websocket.client_state.name != "CONNECTED":
                    logger.info(f"WebSocket not connected, breaking loop: {websocket.client_state.name}")
                    break
                
                # Receive message (can be text JSON or binary)
                # Wrap receive() to catch disconnect errors immediately
                try:
                    message = await websocket.receive()
                except RuntimeError as receive_error:
                    # Handle "Cannot call receive once a disconnect message has been received"
                    if "disconnect" in str(receive_error).lower():
                        logger.info(f"WebSocket disconnect detected during receive: call_id={call_id}")
                        break
                    raise  # Re-raise if it's a different RuntimeError
                
                if "text" in message:
                    # Handle control messages
                    try:
                        data = json.loads(message["text"])
                        msg_type = data.get("type")
                        
                        if msg_type == "control":
                            action = data.get("action")
                            if action == "stop":
                                logger.info(f"Stop requested for call_id={call_id}")
                                break
                            elif action == "pause":
                                await websocket.send_json({
                                    "type": "paused",
                                    "message": "Audio ingestion paused"
                                })
                            elif action == "resume":
                                await websocket.send_json({
                                    "type": "resumed",
                                    "message": "Audio ingestion resumed"
                                })
                        elif msg_type == "audio_chunk":
                            # Audio chunk sent as JSON with base64 data
                            audio_b64 = data.get("audio_data")
                            if audio_b64:
                                try:
                                    audio_bytes = base64.b64decode(audio_b64)
                                    logger.debug(f"Received audio chunk {data.get('chunk_index')}, size: {len(audio_bytes)} bytes")
                                    await process_audio_chunk(
                                        websocket, call_id, agent_id, audio_bytes,
                                        data.get("chunk_index", chunk_count),
                                        data.get("timestamp"),
                                        data.get("metadata", {}),
                                        data.get("format", "pcm"),
                                        data.get("sample_rate", 16000),
                                        data.get("channels", 1)
                                    )
                                    chunk_count += 1
                                    logger.debug(f"Processed chunk {chunk_count} for call {call_id}")
                                except Exception as e:
                                    logger.error(f"Error processing audio chunk: {e}", exc_info=True)
                            else:
                                logger.warning("Received audio_chunk message without audio_data")
                                
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON received")
                        continue
                
                elif "bytes" in message:
                    # Handle binary audio data
                    audio_bytes = message["bytes"]
                    await process_audio_chunk(
                        websocket, call_id, agent_id, audio_bytes,
                        chunk_count, None, {}, "pcm", 16000, 1
                    )
                    chunk_count += 1
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: call_id={call_id}")
                break
            except RuntimeError as e:
                # Handle "Cannot call receive once a disconnect message has been received"
                if "disconnect" in str(e).lower():
                    logger.info(f"WebSocket disconnect detected: call_id={call_id}")
                    break
                else:
                    logger.error(f"Runtime error: {e}", exc_info=True)
                    break
            except Exception as e:
                # Check if it's a disconnect-related error
                error_str = str(e).lower()
                if "disconnect" in error_str or "connection" in error_str:
                    logger.info(f"Connection error detected: {e}")
                    break
                
                logger.error(f"Error processing message: {e}", exc_info=True)
                try:
                    # Only send error if WebSocket is still open
                    if websocket.client_state.name == "CONNECTED":
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Processing error: {str(e)}"
                        })
                except Exception:
                    # Ignore errors when trying to send after disconnect
                    pass
    
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        # Don't try to send messages after disconnect
        if websocket.client_state.name == "CONNECTED":
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": f"WebSocket error: {str(e)}"
                })
            except Exception:
                pass
    finally:
        # Cleanup
        if call_id and agent_id:
            session_key = f"{call_id}:{agent_id}"
            active_connections.pop(session_key, None)
            active_sessions.pop(call_id, None)
            logger.info(f"Session ended: call_id={call_id}, chunks_received={chunk_count}")


async def process_audio_chunk(
    websocket: WebSocket,
    call_id: str,
    agent_id: str,
    audio_data: bytes,
    chunk_index: int,
    timestamp: Optional[float],
    metadata: dict,
    format: str,
    sample_rate: int,
    channels: int
):
    """
    Process and queue an audio chunk.
    
    Args:
        websocket: WebSocket connection
        call_id: Call identifier
        agent_id: Agent identifier
        audio_data: Raw audio bytes
        chunk_index: Chunk sequence number
        timestamp: Optional timestamp
        metadata: Additional metadata
        format: Audio format
        sample_rate: Sample rate
        channels: Number of channels
    """
    try:
        # Preprocess audio chunk
        preprocessed = preprocess_audio_chunk(audio_data, format, sample_rate, channels)
        metadata.update(preprocessed)
        
        # Push to Redis Stream
        message_id = redis_client.push_audio_chunk(
            call_id=call_id,
            agent_id=agent_id,
            audio_data=audio_data,
            chunk_index=chunk_index,
            timestamp=timestamp,
            metadata=metadata
        )
        
        if message_id:
            # Send acknowledgment
            logger.debug(f"Pushed chunk {chunk_index} to Redis: {message_id}")
            await websocket.send_json({
                "type": "chunk_acknowledged",
                "chunk_index": chunk_index,
                "message_id": message_id,
                "timestamp": datetime.now().isoformat()
            })
        else:
            logger.warning(f"Failed to push chunk {chunk_index} to Redis")
            await websocket.send_json({
                "type": "chunk_error",
                "chunk_index": chunk_index,
                "message": "Failed to queue audio chunk"
            })
    
    except Exception as e:
        logger.error(f"Error processing audio chunk: {e}", exc_info=True)
        await websocket.send_json({
            "type": "chunk_error",
            "chunk_index": chunk_index,
            "message": f"Processing error: {str(e)}"
        })


@app.get("/sessions")
async def get_active_sessions():
    """Get list of active sessions."""
    return {
        "active_sessions": list(active_sessions.values()),
        "count": len(active_sessions)
    }


@app.get("/transcripts/{call_id}")
async def get_transcripts(call_id: str):
    """Get all transcript chunks for a call."""
    try:
        from database import SessionLocal, MeetingTranscript
        import uuid
        
        db = SessionLocal()
        try:
            # Validate UUID format
            try:
                call_uuid = uuid.UUID(call_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid call_id format")
            
            # Query transcripts
            transcripts = db.query(MeetingTranscript).filter(
                MeetingTranscript.call_id == call_uuid
            ).order_by(MeetingTranscript.chunk_index.asc()).all()
            
            # Convert to dictionaries
            result = [t.to_dict() for t in transcripts]
            
            return {
                "call_id": call_id,
                "count": len(result),
                "transcripts": result
            }
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transcripts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching transcripts: {str(e)}")


@app.websocket("/ws/llm-updates/{call_id}")
async def websocket_llm_updates(websocket: WebSocket, call_id: str):
    """
    WebSocket endpoint for receiving LLM analysis updates.
    
    Frontend can subscribe to real-time LLM insights (summaries, intents, action items).
    """
    await websocket.accept()
    logger.info(f"LLM updates WebSocket connected for call_id={call_id}")
    
    # Create Redis connection for pub/sub
    redis_pubsub = redis_lib.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        decode_responses=True
    )
    pubsub = redis_pubsub.pubsub()
    channel = f"llm_updates:{call_id}"
    pubsub.subscribe(channel)
    
    try:
        while True:
            # Check if WebSocket is still connected
            if websocket.client_state.name != "CONNECTED":
                logger.info(f"WebSocket disconnected (state: {websocket.client_state.name})")
                break
            
            # Check for messages from Redis pub/sub (non-blocking)
            message = pubsub.get_message(timeout=1.0)
            if message and message['type'] == 'message':
                try:
                    # Check connection before sending
                    if websocket.client_state.name == "CONNECTED":
                        data = json.loads(message['data'])
                        await websocket.send_json(data)
                    else:
                        logger.info("WebSocket not connected, skipping message")
                        break
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error sending LLM update: {e}")
            
            # Check for WebSocket disconnect (non-blocking)
            try:
                # Only try to receive if we're still connected
                if websocket.client_state.name == "CONNECTED":
                    await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                else:
                    break
            except asyncio.TimeoutError:
                continue
            except WebSocketDisconnect:
                break
            except RuntimeError as e:
                # Handle "WebSocket is not connected" error
                if "not connected" in str(e).lower() or "accept" in str(e).lower():
                    logger.info("WebSocket connection lost")
                    break
                raise
                
    except WebSocketDisconnect:
        logger.info(f"LLM updates WebSocket disconnected for call_id={call_id}")
    except Exception as e:
        logger.error(f"Error in LLM updates WebSocket: {e}", exc_info=True)
    finally:
        pubsub.unsubscribe(channel)
        pubsub.close()
        redis_pubsub.close()


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    uvicorn.run(
        "api_gateway:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
