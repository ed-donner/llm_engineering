"""
Streaming Processing Layer (Workers consuming Redis Stream)

Processes audio chunks from Redis Stream:
- VAD (Voice Activity Detection): Filter silence
- ASR (faster-whisper): Convert audio to text
- Speaker Diarization (pyannote.audio): Assign speaker labels
- Save to database immediately
- Push to LLM layer
"""

import os
import json
import time
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from io import BytesIO
import numpy as np
import redis
from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    load_dotenv(override=True)

# Audio processing imports
import webrtcvad
from faster_whisper import WhisperModel
import torch

# Optional: pyannote for advanced diarization (can be heavy)
try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    # Logger will be defined later, just set flag for now

# Database imports
from database import save_transcript_chunk, SessionLocal, MeetingTranscript
from utils.retry import retry_with_backoff

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log pyannote availability after logger is defined
if not PYANNOTE_AVAILABLE:
    logger.warning("pyannote.audio not available, using simple speaker tracking")


class AudioProcessor:
    """Handles audio processing pipeline: VAD -> ASR -> Diarization."""
    
    def __init__(self):
        """Initialize audio processing models."""
        self.vad = webrtcvad.Vad(int(os.getenv('VAD_AGGRESSIVENESS', 2)))
        self.sample_rate = 16000  # WebRTC VAD requires 16kHz
        
        # Initialize Whisper model
        whisper_model = os.getenv('WHISPER_MODEL', 'base')
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        compute_type = 'float16' if device == 'cuda' else 'int8'
        
        logger.info(f"Loading Whisper model: {whisper_model} on {device}")
        self.whisper_model = WhisperModel(
            whisper_model,
            device=device,
            compute_type=compute_type
        )
        logger.info("✅ Whisper model loaded")
        
        # Initialize speaker diarization (optional, can be heavy)
        self.diarization_enabled = os.getenv('ENABLE_DIARIZATION', 'false').lower() == 'true'
        self.diarization_pipeline = None
        
        if self.diarization_enabled and PYANNOTE_AVAILABLE:
            try:
                hf_token = os.getenv('HF_TOKEN')
                if hf_token:
                    self.diarization_pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=hf_token
                    )
                    if torch.cuda.is_available():
                        self.diarization_pipeline.to(torch.device("cuda"))
                    logger.info("✅ Speaker diarization pipeline loaded")
                else:
                    logger.warning("HF_TOKEN not set, diarization disabled")
                    self.diarization_enabled = False
            except Exception as e:
                logger.warning(f"Could not load diarization pipeline: {e}")
                self.diarization_enabled = False
        else:
            if self.diarization_enabled:
                logger.warning("pyannote.audio not available, diarization disabled")
                self.diarization_enabled = False
        
        # Simple speaker tracking (fallback)
        self.speaker_counter = {}  # call_id -> speaker counter
    
    def apply_vad(self, audio_bytes: bytes, sample_rate: int = 16000) -> Optional[bytes]:
        """
        Apply Voice Activity Detection to filter silence.
        
        Args:
            audio_bytes: Raw audio bytes (PCM 16-bit)
            sample_rate: Audio sample rate
            
        Returns:
            Filtered audio bytes if speech detected, None otherwise
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # WebRTC VAD requires specific frame sizes
            frame_duration_ms = 10  # 10ms frames
            frame_size = int(sample_rate * frame_duration_ms / 1000)
            
            # Process in frames
            speech_frames = []
            for i in range(0, len(audio_array), frame_size):
                frame = audio_array[i:i + frame_size]
                if len(frame) < frame_size:
                    # Pad last frame
                    frame = np.pad(frame, (0, frame_size - len(frame)), mode='constant')
                
                # Convert to bytes for VAD
                frame_bytes = frame.tobytes()
                
                # Check if frame contains speech
                if self.vad.is_speech(frame_bytes, sample_rate):
                    speech_frames.append(frame)
            
            if not speech_frames:
                return None  # No speech detected
            
            # Concatenate speech frames
            speech_audio = np.concatenate(speech_frames)
            return speech_audio.tobytes()
            
        except Exception as e:
            logger.error(f"VAD error: {e}")
            return audio_bytes  # Return original on error
    
    def transcribe_audio(self, audio_bytes: bytes, sample_rate: int = 16000) -> Dict:
        """
        Transcribe audio using faster-whisper.
        
        Args:
            audio_bytes: Raw audio bytes
            sample_rate: Audio sample rate
            
        Returns:
            Dictionary with transcription results
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
            
            # Normalize to [-1, 1]
            audio_array = audio_array / 32768.0
            
            # Transcribe with Whisper
            segments, info = self.whisper_model.transcribe(
                audio_array,
                language="en",
                task="transcribe",
                beam_size=5,
                vad_filter=True,  # Additional VAD in Whisper
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Collect segments
            text_parts = []
            segments_list = []
            for segment in segments:
                text_parts.append(segment.text)
                segments_list.append({
                    'text': segment.text,
                    'start': segment.start,
                    'end': segment.end,
                    'no_speech_prob': segment.no_speech_prob
                })
            
            full_text = " ".join(text_parts).strip()
            
            return {
                'text': full_text,
                'language': info.language,
                'language_probability': info.language_probability,
                'segments': segments_list
            }
            
        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            return {
                'text': '',
                'error': str(e)
            }
    
    def diarize_audio(self, audio_bytes: bytes, call_id: str, sample_rate: int = 16000) -> str:
        """
        Perform speaker diarization on audio.
        
        Args:
            audio_bytes: Raw audio bytes
            call_id: Call identifier for speaker tracking
            sample_rate: Audio sample rate
            
        Returns:
            Speaker label (e.g., "SPEAKER_00")
        """
        # Use advanced diarization if available
        if self.diarization_enabled and self.diarization_pipeline:
            try:
                # Convert bytes to numpy array
                audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
                audio_array = audio_array / 32768.0
                
                # Create tensor for pyannote
                audio_tensor = torch.from_numpy(audio_array).unsqueeze(0)
                
                # Run diarization
                diarization = self.diarization_pipeline({
                    "waveform": audio_tensor,
                    "sample_rate": sample_rate
                })
                
                # Get most prominent speaker
                speakers = {}
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    if speaker not in speakers:
                        speakers[speaker] = 0
                    speakers[speaker] += turn.end - turn.start
                
                if speakers:
                    dominant_speaker = max(speakers, key=speakers.get)
                    return dominant_speaker
                    
            except Exception as e:
                logger.error(f"Diarization error: {e}")
        
        # Fallback: Simple speaker tracking by call_id
        # In production, use more sophisticated speaker change detection
        if call_id not in self.speaker_counter:
            self.speaker_counter[call_id] = 0
        
        # Increment counter for this call
        self.speaker_counter[call_id] += 1
        
        # For now, alternate between speakers (can be improved with VAD-based detection)
        speaker_num = self.speaker_counter[call_id] % 2
        return f"SPEAKER_{speaker_num:02d}"


class StreamingProcessor:
    """Main processor that consumes Redis Stream and processes audio chunks."""
    
    def __init__(self):
        """Initialize the streaming processor."""
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=False  # Keep binary for audio data
        )
        self.stream_name = os.getenv('REDIS_STREAM_NAME', 'audio_chunks')
        self.llm_stream_name = os.getenv('REDIS_LLM_STREAM_NAME', 'transcript_chunks')
        self.consumer_group = os.getenv('REDIS_CONSUMER_GROUP', 'audio_processors')
        self.consumer_name = os.getenv('REDIS_CONSUMER_NAME', f'processor_{os.getpid()}')
        
        self.audio_processor = AudioProcessor()
        
        # Worker registry (optional, for scaling)
        self.enable_registry = os.getenv('ENABLE_WORKER_REGISTRY', 'false').lower() == 'true'
        if self.enable_registry:
            from utils.scaling import WorkerRegistry, get_worker_id
            self.worker_registry = WorkerRegistry()
            self.worker_id = os.getenv('WORKER_ID', get_worker_id())
            self.worker_registry.register_worker(self.worker_id, 'audio_processor')
        else:
            self.worker_id = self.consumer_name  # Fallback to consumer name
            self.worker_registry = None
        
        # Initialize consumer group
        self._init_consumer_group()
    
    def _init_consumer_group(self):
        """Initialize Redis Stream consumer group."""
        try:
            self.redis_client.xgroup_create(
                name=self.stream_name,
                groupname=self.consumer_group,
                id='0',
                mkstream=True
            )
            logger.info(f"✅ Consumer group '{self.consumer_group}' created/verified")
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group '{self.consumer_group}' already exists")
            else:
                logger.error(f"Error creating consumer group: {e}")
    
    def process_chunk(self, message_id: str, message_data: Dict) -> bool:
        """
        Process a single audio chunk.
        
        Args:
            message_id: Redis message ID
            message_data: Message data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract data
            call_id = message_data.get(b'call_id', b'').decode('utf-8')
            agent_id = message_data.get(b'agent_id', b'').decode('utf-8')
            chunk_index = int(message_data.get(b'chunk_index', b'0').decode('utf-8'))
            timestamp = float(message_data.get(b'timestamp', b'0').decode('utf-8'))
            
            # Get audio data (hex string -> bytes)
            audio_hex = message_data.get(b'audio_data', b'').decode('utf-8')
            audio_bytes = bytes.fromhex(audio_hex)
            
            # Get metadata
            metadata_str = message_data.get(b'metadata', b'{}').decode('utf-8')
            metadata = json.loads(metadata_str) if metadata_str else {}
            sample_rate = metadata.get('sample_rate', 16000)
            
            logger.debug(f"Processing chunk {chunk_index} for call {call_id}")
            
            # Step 1: Apply VAD
            filtered_audio = self.audio_processor.apply_vad(audio_bytes, sample_rate)
            if filtered_audio is None:
                logger.debug(f"No speech detected in chunk {chunk_index}, skipping")
                return True  # Not an error, just silence
            
            # Step 2: Transcribe with ASR
            transcription_result = self.audio_processor.transcribe_audio(filtered_audio, sample_rate)
            original_text = transcription_result.get('text', '')
            
            if not original_text:
                logger.debug(f"No transcription for chunk {chunk_index}")
                return True  # Not an error, just no text
            
            # Step 3: Speaker diarization
            speaker = self.audio_processor.diarize_audio(filtered_audio, call_id, sample_rate)
            
            # Calculate timestamps
            start_time = datetime.fromtimestamp(timestamp)
            duration = len(filtered_audio) / (sample_rate * 2)  # 16-bit = 2 bytes per sample
            end_time = datetime.fromtimestamp(timestamp + duration)
            
            # Step 4: Save to database immediately with retry
            @retry_with_backoff(
                max_attempts=3,
                initial_delay=0.5,
                exceptions=(Exception,)
            )
            def save_to_db():
                return save_transcript_chunk(
                    call_id=call_id,
                    original_text=original_text,
                    cleaned_text=original_text,  # Can be post-processed later
                    speaker=speaker,
                    chunk_index=chunk_index,
                    start_time=start_time,
                    end_time=end_time
                )
            
            try:
                success = save_to_db()
                if not success:
                    logger.error(f"Failed to save chunk {chunk_index} to database after retries")
                    return False
            except Exception as e:
                logger.error(f"Database save failed after retries: {e}")
                return False
            
            logger.info(f"✅ Processed chunk {chunk_index}: {original_text[:50]}...")
            
            # Step 5: Push to LLM layer
            self._push_to_llm_layer(
                call_id=call_id,
                chunk_index=chunk_index,
                text=original_text,
                speaker=speaker,
                start_time=start_time,
                end_time=end_time,
                metadata=transcription_result
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing chunk: {e}", exc_info=True)
            return False
    
    def _push_to_llm_layer(
        self,
        call_id: str,
        chunk_index: int,
        text: str,
        speaker: str,
        start_time: datetime,
        end_time: datetime,
        metadata: dict
    ):
        """Push processed transcript chunk to LLM processing layer with retry."""
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.5,
            exceptions=(redis.exceptions.RedisError,)
        )
        def push_to_redis():
            entry = {
                'call_id': call_id,
                'chunk_index': str(chunk_index),
                'text': text,
                'speaker': speaker,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'metadata': json.dumps(metadata),
                'processed_at': datetime.now().isoformat()
            }
            
            return self.redis_client.xadd(
                self.llm_stream_name,
                entry,
                maxlen=10000
            )
        
        try:
            message_id = push_to_redis()
            logger.debug(f"Pushed chunk {chunk_index} to LLM layer: {message_id}")
        except Exception as e:
            logger.error(f"Error pushing to LLM layer after retries: {e}")
    
    def run(self, batch_size: int = 10, block_ms: int = 1000):
        """
        Main processing loop with heartbeat and error recovery.
        
        Args:
            batch_size: Number of messages to process per batch
            block_ms: Block time in milliseconds when waiting for messages
        """
        logger.info(f"🚀 Starting streaming processor (consumer: {self.consumer_name})")
        logger.info(f"Worker ID: {self.worker_id}")
        logger.info(f"Consuming from stream: {self.stream_name}")
        logger.info(f"Pushing to LLM stream: {self.llm_stream_name}")
        logger.info(f"Worker registry enabled: {self.enable_registry}")
        
        last_heartbeat = time.time()
        heartbeat_interval = 30  # seconds
        
        while True:
            try:
                # Update heartbeat
                if self.enable_registry and (time.time() - last_heartbeat) >= heartbeat_interval:
                    self.worker_registry.update_heartbeat(self.worker_id, 'audio_processor')
                    last_heartbeat = time.time()
                
                # Read messages from stream with retry
                @retry_with_backoff(
                    max_attempts=3,
                    initial_delay=1.0,
                    exceptions=(redis.exceptions.ConnectionError,)
                )
                def read_messages():
                    return self.redis_client.xreadgroup(
                        groupname=self.consumer_group,
                        consumername=self.consumer_name,
                        streams={self.stream_name: '>'},
                        count=batch_size,
                        block=block_ms
                    )
                
                messages = read_messages()
                
                if not messages:
                    continue
                
                # Process each message
                stream_name, stream_messages = messages[0]
                
                for message_id, message_data in stream_messages:
                    success = self.process_chunk(message_id.decode(), message_data)
                    
                    if success:
                        # Acknowledge message with retry
                        @retry_with_backoff(
                            max_attempts=3,
                            initial_delay=0.5,
                            exceptions=(redis.exceptions.RedisError,)
                        )
                        def ack_message():
                            self.redis_client.xack(
                                self.stream_name,
                                self.consumer_group,
                                message_id
                            )
                        
                        try:
                            ack_message()
                        except Exception as e:
                            logger.error(f"Failed to acknowledge message after retries: {e}")
                    else:
                        logger.warning(f"Failed to process message {message_id}, will retry")
                        # In production, implement retry logic or dead letter queue
                
            except redis.exceptions.ConnectionError as e:
                logger.error(f"Redis connection error: {e}")
                logger.info("Retrying in 5 seconds...")
                time.sleep(5)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                if self.enable_registry and self.worker_registry:
                    self.worker_registry.unregister_worker(self.worker_id, 'audio_processor')
                break
            except Exception as e:
                logger.error(f"Unexpected error in processing loop: {e}", exc_info=True)
                time.sleep(1)


def main():
    """Main entry point."""
    processor = StreamingProcessor()
    
    try:
        processor.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        logger.info("Processor shutdown complete")


if __name__ == "__main__":
    main()
