"""
Pydantic Models for Request/Response Validation

Data models for WebSocket messages and API requests.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class AudioChunkRequest(BaseModel):
    """Model for incoming audio chunk data."""
    call_id: str = Field(..., description="Unique call/meeting identifier")
    agent_id: str = Field(..., description="Agent identifier")
    chunk_index: int = Field(..., description="Sequential chunk number")
    audio_data: bytes = Field(..., description="Raw audio bytes (base64 or hex)")
    timestamp: Optional[float] = Field(None, description="Unix timestamp")
    metadata: Optional[dict] = Field(None, description="Additional metadata")
    format: Optional[str] = Field("pcm", description="Audio format (pcm, opus, etc.)")
    sample_rate: Optional[int] = Field(16000, description="Audio sample rate")
    channels: Optional[int] = Field(1, description="Number of audio channels")


class SessionInfo(BaseModel):
    """Model for session information."""
    call_id: str
    agent_id: str
    created_at: datetime
    status: str = "active"


class WebSocketMessage(BaseModel):
    """Model for WebSocket message structure."""
    type: str = Field(..., description="Message type (audio_chunk, control, etc.)")
    data: dict = Field(..., description="Message payload")
    timestamp: Optional[float] = Field(None, description="Message timestamp")


class ControlMessage(BaseModel):
    """Model for control messages (start, stop, pause)."""
    action: str = Field(..., description="Action: start, stop, pause, resume")
    call_id: str = Field(..., description="Call identifier")
    agent_id: str = Field(..., description="Agent identifier")


class StatusResponse(BaseModel):
    """Model for status responses."""
    status: str
    message: str
    call_id: Optional[str] = None
    chunks_received: Optional[int] = None
