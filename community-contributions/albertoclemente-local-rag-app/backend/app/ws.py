"""
WebSocket endpoint for streaming LLM responses.
Implements the exact streaming protocol specified in the LLD.
"""

import asyncio
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query as WSQuery
from fastapi.websockets import WebSocketState

from app.conversation import get_conversation_manager

from app.models import (
    StartEvent,
    TokenEvent,
    CitationEvent,
    SourcesEvent,
    EndEvent,
    ErrorEvent,
    StreamEvent
)
from app.diagnostics import get_logger
from .llm import get_llm_service
from .retrieval import get_retrieval_service

logger = get_logger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for streaming"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept a WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connected: {connection_id}")
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_event(self, connection_id: str, event: StreamEvent):
        """Send a streaming event to a specific connection"""
        if connection_id not in self.active_connections:
            logger.warning(f"Connection not found: {connection_id}")
            return
        
        websocket = self.active_connections[connection_id]
        if websocket.client_state == WebSocketState.DISCONNECTED:
            self.disconnect(connection_id)
            return
        
        try:
            # Convert Pydantic model to dict and send as JSON
            event_data = event.dict(by_alias=True)
            await websocket.send_text(json.dumps(event_data))
            logger.debug(f"Sent event {event.event} to {connection_id}")
        except Exception as e:
            logger.error(f"Error sending event to {connection_id}: {e}")
            self.disconnect(connection_id)


# Global connection manager
manager = ConnectionManager()

# Simple query storage for session/turn coordination
_query_store: Dict[str, str] = {}


def store_query(session_id: str, turn_id: str, query: str):
    """Store a query for later retrieval by WebSocket handler"""
    key = f"{session_id}:{turn_id}"
    _query_store[key] = query
    logger.debug(f"Stored query for {key}: {query}")


def get_stored_query(session_id: str, turn_id: str) -> Optional[str]:
    """Retrieve a stored query"""
    key = f"{session_id}:{turn_id}"
    query = _query_store.pop(key, None)
    if query:
        logger.debug(f"Retrieved query for {key}: {query}")
    return query


async def process_streaming_query(
    session_id: str, 
    turn_id: str, 
    query: str,
    connection_id: str
):
    """
    Process a query and stream the LLM response.
    
    This is the core RAG pipeline with streaming:
    1. Send START event
    2. Perform retrieval
    3. Send CITATION events
    4. Stream LLM tokens
    5. Send END event
    """
    try:
        logger.info(f"Processing streaming query for session {session_id}, turn {turn_id}: {query}")
        
        # Get services
        retrieval_service = await get_retrieval_service()
        llm_service = await get_llm_service()
        
        # Get model info for START event
        health_info = await llm_service.health_check()
        model_name = health_info.get("model", "unknown")
        
        # Send START event
        start_event = StartEvent(meta={"model": model_name})
        await manager.send_event(connection_id, start_event)
        
        # Perform retrieval
        logger.info(f"🔍 WS DEBUG: About to call retrieve_for_query for: {query}")
        retrieval_result = await retrieval_service.retrieve_for_query(query)
        logger.info(f"🔍 WS DEBUG: Retrieval completed. Found {len(retrieval_result.chunks)} chunks")
        
        # Send CITATION events for retrieved chunks
        for i, chunk in enumerate(retrieval_result.chunks, 1):
            citation_event = CitationEvent(
                label=i, 
                chunkId=f"{chunk.doc_id}#{chunk.chunk_id}"
            )
            await manager.send_event(connection_id, citation_event)
        
        # Send SOURCES event with detailed source information
        if retrieval_result.chunks:
            sources_info = [
                {
                    "document": chunk.doc_id,
                    "content": chunk.text[:100] + "..." if len(chunk.text) > 100 else chunk.text,
                    "score": chunk.score
                }
                for chunk in retrieval_result.chunks
            ]
            sources_event = SourcesEvent(sources=sources_info)
            await manager.send_event(connection_id, sources_event)
        
        # Get conversation context
        conversation_mgr = get_conversation_manager()
        conversation_context = conversation_mgr.get_context_for_query(session_id)
        
        # Start LLM streaming
        logger.info(f"Starting LLM generation for query: {query}")
        if conversation_context:
            logger.info(f"Using conversation context for session {session_id}")
        
        token_count = 0
        start_time = asyncio.get_event_loop().time()
        full_response_parts = []
        
        async for stream_token in llm_service.generate_stream(query, retrieval_result, conversation_context):
            if stream_token.text:
                token_event = TokenEvent(text=stream_token.text)
                await manager.send_event(connection_id, token_event)
                token_count += 1
                full_response_parts.append(stream_token.text)
            
            # Check if generation is complete
            if stream_token.is_final:
                break
        
        # Calculate timing
        end_time = asyncio.get_event_loop().time()
        generation_time_ms = int((end_time - start_time) * 1000)
        
        # Send END event with stats
        end_event = EndEvent(stats={
            "tokens": token_count,
            "ms": generation_time_ms,
            "retrieval_chunks": len(retrieval_result.chunks),
            "retrieval_time": retrieval_result.retrieval_time,
            "coverage_score": retrieval_result.coverage_score,
            "query_complexity": retrieval_result.query_complexity.value
        })
        await manager.send_event(connection_id, end_event)
        
        # Add this conversation turn to the session history
        full_response = ''.join(full_response_parts)
        # Reuse the sources_info created earlier during SOURCES event
        if retrieval_result.chunks:
            sources_info = [
                {
                    "document": chunk.doc_id,
                    "content": chunk.text[:100] + "..." if len(chunk.text) > 100 else chunk.text,
                    "score": chunk.score
                }
                for chunk in retrieval_result.chunks
            ]
        else:
            sources_info = []
        conversation_mgr.add_turn(session_id, turn_id, query, full_response, sources_info)
        
        logger.info(f"Completed streaming for session {session_id}, turn {turn_id} - {token_count} tokens in {generation_time_ms}ms")
        
    except Exception as e:
        logger.error(f"Error in streaming query: {e}")
        error_event = ErrorEvent(
            error_code="STREAMING_ERROR", 
            detail=str(e)
        )
        await manager.send_event(connection_id, error_event)


@router.websocket("/ws/stream")
async def websocket_stream(
    websocket: WebSocket,
    session_id: str = WSQuery(...),
    turn_id: str = WSQuery(...)
):
    """
    WebSocket endpoint for streaming LLM responses.
    
    Query parameters:
    - session_id: Chat session identifier
    - turn_id: Specific turn/query identifier
    
    Events sent:
    - START: {"event": "START", "meta": {"model": "model_name"}}
    - TOKEN: {"event": "TOKEN", "text": "..."}
    - CITATION: {"event": "CITATION", "label": 1, "chunkId": "doc#000123"}
    - END: {"event": "END", "stats": {"tokens": N, "ms": T}}
    - ERROR: {"event": "ERROR", "error_code": "...", "detail": "..."}
    """
    connection_id = f"{session_id}:{turn_id}"
    
    try:
        await manager.connect(websocket, connection_id)
        
        # Get the actual query from storage
        query = get_stored_query(session_id, turn_id)
        if not query:
            # If no query found, send error and close
            error_event = ErrorEvent(
                error_code="QUERY_NOT_FOUND",
                detail=f"No query found for session {session_id}, turn {turn_id}"
            )
            await manager.send_event(connection_id, error_event)
            return
        
        # Process the query and stream the response
        await process_streaming_query(session_id, turn_id, query, connection_id)
        
        # Keep connection alive until client disconnects
        while True:
            try:
                # Wait for client messages (though we don't expect any in this protocol)
                data = await websocket.receive_text()
                logger.debug(f"Received unexpected message from client: {data}")
            except WebSocketDisconnect:
                break
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        if connection_id in manager.active_connections:
            error_event = ErrorEvent(
                error_code="CONNECTION_ERROR",
                detail=str(e)
            )
            await manager.send_event(connection_id, error_event)
    finally:
        manager.disconnect(connection_id)


async def start_streaming_for_query(session_id: str, turn_id: str, query: str):
    """
    Start streaming for a query. This should be called after the WebSocket
    connection is established and the query has been initiated via REST API.
    """
    connection_id = f"{session_id}:{turn_id}"
    
    # The actual streaming will happen in the WebSocket handler
    # This function exists for coordination between REST API and WebSocket
    logger.info(f"Streaming started for query: {session_id}:{turn_id}")
    
    # Store the query for the WebSocket handler
    store_query(session_id, turn_id, query)


# Connection monitoring and management
async def get_active_connections() -> Dict[str, Any]:
    """Get information about active WebSocket connections"""
    return {
        "active_count": len(manager.active_connections),
        "connections": list(manager.active_connections.keys())
    }


async def cleanup_stale_queries():
    """Clean up queries that haven't been processed"""
    # This could be called periodically to clean up old stored queries
    # For now, it's just a placeholder
    global _query_store
    if len(_query_store) > 100:  # Arbitrary threshold
        logger.warning(f"Query store has {len(_query_store)} entries, consider cleanup")


# TODO: Add functions for:
# - Managing active streaming sessions with timeouts
# - Canceling ongoing streams
# - Handling connection timeouts and reconnection
# - Rate limiting per session/IP
# - Metrics collection for WebSocket performance

# Export key functions and classes
__all__ = [
    "router",
    "ConnectionManager", 
    "manager",
    "process_streaming_query",
    "start_streaming_for_query",
    "store_query",
    "get_stored_query",
    "get_active_connections",
    "cleanup_stale_queries"
]
