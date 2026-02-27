"""
Audio storage utilities for persisting raw audio for debugging/reprocessing.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)


class AudioStorage:
    """Handles persistence of raw audio chunks for debugging/reprocessing."""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize audio storage.
        
        Args:
            base_path: Base directory for storing audio files (default: ./audio_storage)
        """
        self.base_path = Path(base_path or os.getenv('AUDIO_STORAGE_PATH', './audio_storage'))
        self.enabled = os.getenv('ENABLE_AUDIO_STORAGE', 'false').lower() == 'true'
        
        if self.enabled:
            self.base_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Audio storage enabled at: {self.base_path}")
        else:
            logger.info("Audio storage disabled")
    
    def save_audio_chunk(
        self,
        call_id: str,
        chunk_index: int,
        audio_data: bytes,
        metadata: Optional[dict] = None
    ) -> Optional[str]:
        """
        Save an audio chunk to disk.
        
        Args:
            call_id: Call identifier
            chunk_index: Chunk sequence number
            audio_data: Raw audio bytes
            metadata: Additional metadata
            
        Returns:
            File path if saved, None otherwise
        """
        if not self.enabled:
            return None
        
        try:
            # Create call-specific directory
            call_dir = self.base_path / call_id
            call_dir.mkdir(parents=True, exist_ok=True)
            
            # Save audio file
            audio_file = call_dir / f"chunk_{chunk_index:06d}.pcm"
            with open(audio_file, 'wb') as f:
                f.write(audio_data)
            
            # Save metadata
            if metadata:
                metadata_file = call_dir / f"chunk_{chunk_index:06d}.json"
                metadata['saved_at'] = datetime.now().isoformat()
                metadata['file_path'] = str(audio_file)
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            return str(audio_file)
            
        except Exception as e:
            logger.error(f"Error saving audio chunk: {e}", exc_info=True)
            return None
    
    def load_audio_chunk(self, call_id: str, chunk_index: int) -> Optional[bytes]:
        """
        Load an audio chunk from disk.
        
        Args:
            call_id: Call identifier
            chunk_index: Chunk sequence number
            
        Returns:
            Audio bytes if found, None otherwise
        """
        if not self.enabled:
            return None
        
        try:
            audio_file = self.base_path / call_id / f"chunk_{chunk_index:06d}.pcm"
            if audio_file.exists():
                with open(audio_file, 'rb') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error loading audio chunk: {e}")
        
        return None
    
    def get_call_audio_files(self, call_id: str) -> list:
        """
        Get list of audio files for a call.
        
        Args:
            call_id: Call identifier
            
        Returns:
            List of audio file paths
        """
        if not self.enabled:
            return []
        
        try:
            call_dir = self.base_path / call_id
            if call_dir.exists():
                return sorted([str(f) for f in call_dir.glob("chunk_*.pcm")])
        except Exception as e:
            logger.error(f"Error listing audio files: {e}")
        
        return []
    
    def cleanup_old_calls(self, days: int = 7):
        """
        Clean up audio files older than specified days.
        
        Args:
            days: Number of days to keep files
        """
        if not self.enabled:
            return
        
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=days)
            
            for call_dir in self.base_path.iterdir():
                if call_dir.is_dir():
                    # Check modification time
                    mtime = datetime.fromtimestamp(call_dir.stat().st_mtime)
                    if mtime < cutoff_time:
                        import shutil
                        shutil.rmtree(call_dir)
                        logger.info(f"Cleaned up old call directory: {call_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up old calls: {e}")


# Global instance
audio_storage = AudioStorage()
