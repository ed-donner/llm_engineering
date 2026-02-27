"""
Redis Stream Client for Real-Time Audio Processing

Handles pushing audio chunks to Redis Streams for asynchronous processing.
"""

import redis
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    load_dotenv(override=True)


class RedisStreamClient:
    """Client for managing Redis Stream operations."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True,
            socket_connect_timeout=5
        )
        self.stream_name = os.getenv('REDIS_STREAM_NAME', 'audio_chunks')
        
    def ping(self) -> bool:
        """Check Redis connection."""
        try:
            return self.redis_client.ping()
        except Exception as e:
            print(f"Redis ping failed: {e}")
            return False
    
    def push_audio_chunk(
        self,
        call_id: str,
        agent_id: str,
        audio_data: bytes,
        chunk_index: int,
        timestamp: Optional[float] = None,
        metadata: Optional[dict] = None
    ) -> Optional[str]:
        """
        Push an audio chunk to Redis Stream.
        
        Args:
            call_id: Unique call/meeting identifier
            agent_id: Agent identifier
            audio_data: Raw audio bytes
            chunk_index: Sequential chunk number
            timestamp: Unix timestamp (defaults to now)
            metadata: Additional metadata dictionary
            
        Returns:
            Message ID if successful, None otherwise
        """
        try:
            if timestamp is None:
                timestamp = datetime.now().timestamp()
            
            # Prepare stream entry
            entry = {
                'call_id': call_id,
                'agent_id': agent_id,
                'chunk_index': str(chunk_index),
                'timestamp': str(timestamp),
                'audio_data': audio_data.hex(),  # Convert bytes to hex string for Redis
                'data_size': str(len(audio_data)),
            }
            
            # Add metadata if provided
            if metadata:
                entry['metadata'] = json.dumps(metadata)
            
            # Add to Redis Stream
            message_id = self.redis_client.xadd(
                self.stream_name,
                entry,
                maxlen=10000  # Keep last 10k messages
            )
            
            return message_id
            
        except redis.RedisError as e:
            print(f"Error pushing to Redis Stream: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in push_audio_chunk: {e}")
            return None
    
    def get_stream_info(self) -> dict:
        """Get information about the Redis Stream."""
        try:
            info = self.redis_client.xinfo_stream(self.stream_name)
            return {
                'length': info.get('length', 0),
                'first_entry': info.get('first-entry'),
                'last_entry': info.get('last-entry'),
            }
        except redis.RedisError as e:
            print(f"Error getting stream info: {e}")
            return {}
    
    def close(self):
        """Close Redis connection."""
        if self.redis_client:
            self.redis_client.close()


# Global instance
redis_client = RedisStreamClient()
