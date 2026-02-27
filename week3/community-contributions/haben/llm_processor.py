"""
Streaming LLM Processor

Reads transcript chunks from Redis Stream and generates:
- Running summary
- Intent detection
- Complaint classification
- Action item extraction
- Streams results via WebSocket to frontend
- Updates database with LLM summaries
"""

import os
import json
import time
import logging
import redis
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
from dotenv import load_dotenv
from openai import OpenAI
import uuid

# Optional: Hugging Face support
try:
    from huggingface_hub import InferenceClient
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

# Database imports
from database import SessionLocal, MeetingTranscript
from utils.retry import retry_with_backoff

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


class LLMAnalyzer:
    """Handles LLM-based analysis of transcript chunks."""
    
    def __init__(self):
        """Initialize LLM client."""
        # Support multiple LLM providers in priority order:
        # 1. Ollama (local, open source)
        # 2. Hugging Face (local or cloud)
        # 3. OpenRouter (cloud)
        # 4. OpenAI (cloud)
        
        use_ollama = os.getenv('USE_OLLAMA', 'true').lower() == 'true'
        use_huggingface = os.getenv('USE_HUGGINGFACE', 'false').lower() == 'true'
        ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434/v1')
        
        if use_ollama and not use_huggingface:
            # Ollama runs locally and uses OpenAI-compatible API
            # No API key needed for local Ollama
            self.client = OpenAI(
                api_key="ollama",  # Ollama doesn't require a real API key
                base_url=ollama_base_url
            )
            # Default Ollama models: llama3, mistral, llama3.2, etc.
            self.model = os.getenv('LLM_MODEL', 'llama3.2')
            self.provider = 'ollama'
            logger.info(f"Using Ollama (Open Source) API at {ollama_base_url} with model: {self.model}")
        elif use_huggingface:
            # Hugging Face Inference API
            if not HF_AVAILABLE:
                raise ImportError("huggingface_hub is required for Hugging Face. Install with: pip install huggingface_hub")
            
            hf_token = os.getenv('HUGGINGFACE_API_KEY')
            hf_endpoint = os.getenv('HUGGINGFACE_ENDPOINT')  # Optional: custom endpoint
            
            if hf_endpoint:
                # Custom endpoint (e.g., local inference server)
                self.client = InferenceClient(endpoint=hf_endpoint, token=hf_token)
            else:
                # Standard Hugging Face Inference API
                self.client = InferenceClient(token=hf_token)
            
            # Default Hugging Face models
            self.model = os.getenv('LLM_MODEL', 'meta-llama/Llama-3.2-3B-Instruct')
            self.provider = 'huggingface'
            logger.info(f"Using Hugging Face API with model: {self.model}")
        else:
            # Check for OpenRouter or OpenAI
            api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY or OPENAI_API_KEY must be set when USE_OLLAMA=false and USE_HUGGINGFACE=false")
            
            # Check if using OpenRouter
            use_openrouter = os.getenv('OPENROUTER_API_KEY') is not None
            
            if use_openrouter:
                # OpenRouter uses OpenAI-compatible API with different base URL
                default_headers = {
                    "HTTP-Referer": os.getenv('OPENROUTER_HTTP_REFERER', 'https://github.com/your-repo'),
                    "X-Title": os.getenv('OPENROUTER_APP_NAME', 'Call Center AI')
                }
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://openrouter.ai/api/v1",
                    default_headers=default_headers
                )
                self.model = os.getenv('LLM_MODEL', 'openai/gpt-3.5-turbo')
                self.provider = 'openrouter'
                logger.info(f"Using OpenRouter API with model: {self.model}")
            else:
                # Standard OpenAI
                self.client = OpenAI(api_key=api_key)
                self.model = os.getenv('LLM_MODEL', 'gpt-4-turbo-preview')
                self.provider = 'openai'
                logger.info(f"Using OpenAI API with model: {self.model}")
        
        # Configure context and tokens based on provider
        if use_ollama and not use_huggingface:
            self.max_context_chunks = int(os.getenv('LLM_CONTEXT_CHUNKS', '8'))  # More chunks for better context
            self.max_tokens = int(os.getenv('LLM_MAX_TOKENS', '1500'))  # More tokens for detailed responses
        elif use_huggingface:
            self.max_context_chunks = int(os.getenv('LLM_CONTEXT_CHUNKS', '8'))  # Hugging Face models also benefit
            self.max_tokens = int(os.getenv('LLM_MAX_TOKENS', '1500'))
        else:
            self.max_context_chunks = int(os.getenv('LLM_CONTEXT_CHUNKS', '5'))
            self.max_tokens = int(os.getenv('LLM_MAX_TOKENS', '800'))
        
        self.analysis_interval = int(os.getenv('LLM_ANALYSIS_INTERVAL', '10'))  # seconds
        
    def generate_analysis_prompt(self, transcript_chunks: List[Dict]) -> str:
        """
        Generate prompt for LLM analysis.
        
        Args:
            transcript_chunks: List of transcript chunks with text, speaker, timestamps
            
        Returns:
            Formatted prompt string
        """
        # Format transcript
        transcript_text = ""
        for chunk in transcript_chunks:
            speaker = chunk.get('speaker', 'UNKNOWN')
            text = chunk.get('text', '')
            timestamp = chunk.get('start_time', '')
            transcript_text += f"[{timestamp}] {speaker}: {text}\n"
        
        # Check if using Ollama (needs more explicit instructions)
        use_ollama = os.getenv('USE_OLLAMA', 'true').lower() == 'true'
        
        if use_ollama:
            # Ollama models work better with more structured prompts
            prompt = f"""You are a call center analyst. Analyze this conversation transcript and return ONLY valid JSON.

Transcript:
{transcript_text}

Analyze and return JSON with:
- summary: 2-3 sentence summary of the conversation
- intent: object with type (question|complaint|request|information|support|other), confidence (0.0-1.0), description
- complaint: object with is_complaint (boolean), type (billing|technical|service|product|other|null), severity (low|medium|high|null), description
- action_items: array of objects with item, assignee, priority (low|medium|high), due_date
- sentiment: positive|neutral|negative
- key_topics: array of topic strings

Return ONLY valid JSON, no other text:
{{
  "summary": "Brief summary here",
  "intent": {{
    "type": "question",
    "confidence": 0.8,
    "description": "Brief intent description"
  }},
  "complaint": {{
    "is_complaint": false,
    "type": null,
    "severity": null,
    "description": ""
  }},
  "action_items": [
    {{
      "item": "Action description if any",
      "assignee": "Person responsible if mentioned",
      "priority": "low",
      "due_date": "Date if mentioned"
    }}
  ],
  "sentiment": "neutral",
  "key_topics": ["topic1", "topic2"]
}}"""
        else:
            # More concise for cloud APIs
            prompt = f"""Analyze transcript, return JSON only:

{transcript_text}

{{
"summary":"2-3 sentence summary",
"intent":{{"type":"question|complaint|request|information|support|other","confidence":0.0-1.0,"description":"brief"}},
"complaint":{{"is_complaint":false,"type":"billing|technical|service|product|other|null","severity":"low|medium|high|null","description":""}},
"action_items":[{{"item":"","assignee":"","priority":"low|medium|high","due_date":""}}],
"sentiment":"positive|neutral|negative",
"key_topics":[]
}}"""
        
        return prompt
    
    def analyze_transcript(self, transcript_chunks: List[Dict], stream: bool = False):
        """
        Analyze transcript chunks using LLM.
        
        Args:
            transcript_chunks: List of transcript chunks
            stream: Whether to stream the response
            
        Returns:
            Analysis results as dictionary or stream generator
        """
        if not transcript_chunks:
            return {
                "summary": "No transcript available yet.",
                "intent": {"type": "other", "confidence": 0.0, "description": "No data"},
                "complaint": {"is_complaint": False},
                "action_items": [],
                "sentiment": "neutral",
                "key_topics": []
            }
        
        prompt = self.generate_analysis_prompt(transcript_chunks)
        
        # Prepare messages based on provider
        use_ollama = os.getenv('USE_OLLAMA', 'true').lower() == 'true'
        use_huggingface = os.getenv('USE_HUGGINGFACE', 'false').lower() == 'true'
        
        if use_ollama and not use_huggingface:
            messages = [
                {
                    "role": "system",
                    "content": "You are a professional call center analyst. You analyze customer conversations and extract structured insights. Always respond with valid JSON only. Do not include any text before or after the JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        elif use_huggingface:
            # Hugging Face uses a different format - pass prompt directly
            messages = [
                {
                    "role": "system",
                    "content": "You are a professional call center analyst. You analyze customer conversations and extract structured insights. Always respond with valid JSON only. Do not include any text before or after the JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        else:
            messages = [
                {
                    "role": "system",
                    "content": "Call center analyst. Return JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        
        if stream:
            return self._stream_analysis(messages)
        else:
            return self._get_analysis(messages, prompt)
    
    def _get_analysis(self, messages: List[Dict], prompt: str = None) -> Dict:
        """Get non-streaming analysis."""
        try:
            # Handle Hugging Face differently
            if self.provider == 'huggingface':
                # Hugging Face Inference API format
                # Convert messages to prompt format
                prompt_text = ""
                for msg in messages:
                    if msg['role'] == 'system':
                        prompt_text += f"System: {msg['content']}\n\n"
                    elif msg['role'] == 'user':
                        prompt_text += f"User: {msg['content']}\n\n"
                full_prompt = prompt_text.strip()
                
                response = self.client.text_generation(
                    full_prompt,
                    max_new_tokens=self.max_tokens,
                    temperature=0.3,
                    return_full_text=False
                )
                content = response
            else:
                # OpenAI-compatible API (Ollama, OpenRouter, OpenAI)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,
                    response_format={"type": "json_object"},
                    max_tokens=self.max_tokens
                )
                content = response.choices[0].message.content
            
            # Ollama sometimes returns JSON wrapped in markdown or with extra text
            # Try to extract JSON from the response
            content = content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            elif content.startswith("```"):
                content = content[3:]  # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove closing ```
            
            content = content.strip()
            
            # Try to find JSON object in the response
            try:
                # First try direct parsing
                return json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON object from text
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    raise ValueError(f"Could not parse JSON from response: {content[:200]}")
            
        except Exception as e:
            error_str = str(e)
            # Handle OpenRouter credit limit errors
            if "402" in error_str or "credits" in error_str.lower() or "Payment Required" in error_str:
                logger.warning(f"OpenRouter credit limit reached: {e}")
                return {
                    "error": "Insufficient OpenRouter credits. Please add credits at https://openrouter.ai/settings/keys",
                    "summary": "Analysis unavailable - insufficient API credits",
                    "intent": {"type": "other", "confidence": 0.0, "description": "Analysis unavailable"},
                    "complaint": {"is_complaint": False},
                    "action_items": [],
                    "sentiment": "neutral",
                    "key_topics": []
                }
            
            logger.error(f"Error in LLM analysis: {e}", exc_info=True)
            return {
                "error": str(e),
                "summary": "Analysis failed",
                "intent": {"type": "other", "confidence": 0.0},
                "complaint": {"is_complaint": False},
                "action_items": [],
                "sentiment": "neutral",
                "key_topics": []
            }
    
    def _stream_analysis(self, messages: List[Dict]):
        """Stream analysis results."""
        try:
            # Hugging Face doesn't support streaming the same way
            if self.provider == 'huggingface':
                # For Hugging Face, use non-streaming (streaming not well supported)
                return self._get_analysis(messages)
            
            # OpenAI-compatible API (Ollama, OpenRouter, OpenAI)
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                stream=True,
                max_tokens=self.max_tokens
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # Try to parse final JSON
            try:
                parsed = json.loads(full_response)
                yield json.dumps(parsed)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error in streaming analysis: {e}", exc_info=True)
            yield json.dumps({"error": str(e)})


class LLMProcessor:
    """Main processor that consumes transcript chunks and generates LLM insights."""
    
    def __init__(self):
        """Initialize the LLM processor."""
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        self.stream_name = os.getenv('REDIS_LLM_STREAM_NAME', 'transcript_chunks')
        self.consumer_group = os.getenv('REDIS_LLM_CONSUMER_GROUP', 'llm_processors')
        self.consumer_name = os.getenv('REDIS_LLM_CONSUMER_NAME', f'llm_processor_{os.getpid()}')
        
        # WebSocket connection manager (will be set by API Gateway integration)
        self.websocket_manager = None
        
        self.llm_analyzer = LLMAnalyzer()
        
        # Store transcript buffers per call_id
        self.transcript_buffers: Dict[str, List[Dict]] = defaultdict(list)
        
        # Store last analysis time per call_id
        self.last_analysis_time: Dict[str, float] = {}
        
        # Batch processing configuration
        self.batch_size = int(os.getenv('LLM_BATCH_SIZE', '20'))  # Chunks per batch
        self.batch_timeout = int(os.getenv('LLM_BATCH_TIMEOUT', '30'))  # Seconds
        self.batch_timers: Dict[str, float] = {}  # Track batch start times
        
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
            logger.info(f"✅ LLM Consumer group '{self.consumer_group}' created/verified")
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group '{self.consumer_group}' already exists")
            else:
                logger.error(f"Error creating consumer group: {e}")
    
    def set_websocket_manager(self, manager):
        """Set WebSocket manager for sending updates to frontend."""
        self.websocket_manager = manager
    
    def process_chunk(self, message_id: str, message_data: Dict) -> bool:
        """
        Process a transcript chunk.
        
        Args:
            message_id: Redis message ID
            message_data: Message data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract data
            call_id = message_data.get('call_id', '')
            chunk_index = int(message_data.get('chunk_index', '0'))
            text = message_data.get('text', '')
            speaker = message_data.get('speaker', 'UNKNOWN')
            start_time = message_data.get('start_time', '')
            end_time = message_data.get('end_time', '')
            
            if not call_id or not text:
                logger.warning(f"Invalid chunk data: call_id={call_id}, text={text[:50]}")
                return True  # Skip invalid chunks
            
            # Add to buffer
            chunk_data = {
                'chunk_index': chunk_index,
                'text': text,
                'speaker': speaker,
                'start_time': start_time,
                'end_time': end_time,
                'processed_at': datetime.now().isoformat()
            }
            
            self.transcript_buffers[call_id].append(chunk_data)
            
            # Keep only recent chunks (sliding window)
            max_chunks = self.llm_analyzer.max_context_chunks
            if len(self.transcript_buffers[call_id]) > max_chunks:
                self.transcript_buffers[call_id] = self.transcript_buffers[call_id][-max_chunks:]
            
            # Check if we should analyze (time-based, chunk-based, or batch-based)
            current_time = time.time()
            last_time = self.last_analysis_time.get(call_id, 0)
            time_since_last = current_time - last_time
            buffer_size = len(self.transcript_buffers[call_id])
            
            # Batch processing: analyze when batch size reached or timeout
            batch_start = self.batch_timers.get(call_id, current_time)
            batch_age = current_time - batch_start
            
            should_analyze = (
                time_since_last >= self.llm_analyzer.analysis_interval or
                buffer_size >= max_chunks or
                buffer_size >= self.batch_size or
                (buffer_size > 0 and batch_age >= self.batch_timeout)
            )
            
            if should_analyze:
                self._analyze_and_update(call_id)
                self.last_analysis_time[call_id] = current_time
                # Reset batch timer
                if buffer_size >= self.batch_size:
                    self.batch_timers[call_id] = current_time
            elif call_id not in self.batch_timers:
                # Start batch timer for new calls
                self.batch_timers[call_id] = current_time
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing chunk: {e}", exc_info=True)
            return False
    
    def _analyze_and_update(self, call_id: str):
        """Analyze transcript buffer and update frontend/database."""
        try:
            chunks = self.transcript_buffers.get(call_id, [])
            if not chunks:
                return
            
            logger.info(f"Analyzing {len(chunks)} chunks for call {call_id}")
            
            # Get LLM analysis with retry
            @retry_with_backoff(
                max_attempts=3,
                initial_delay=1.0,
                exceptions=(Exception,)
            )
            def get_analysis():
                return self.llm_analyzer.analyze_transcript(chunks, stream=False)
            
            analysis = get_analysis()
            
            # Send to frontend via WebSocket
            self._send_to_frontend(call_id, analysis)
            
            # Update database with retry
            @retry_with_backoff(
                max_attempts=3,
                initial_delay=0.5,
                exceptions=(Exception,)
            )
            def update_db():
                self._update_database(call_id, analysis, chunks)
            
            update_db()
            
            logger.info(f"✅ Analysis complete for call {call_id}")
            
        except Exception as e:
            logger.error(f"Error in analysis: {e}", exc_info=True)
    
    def _send_to_frontend(self, call_id: str, analysis: Dict):
        """Send analysis results to frontend via WebSocket."""
        if not self.websocket_manager:
            # Try to get from API Gateway if available
            try:
                from api_gateway import active_connections
                session_key = None
                for key, ws in active_connections.items():
                    if call_id in key:
                        session_key = key
                        break
                
                if session_key and session_key in active_connections:
                    # Send via existing WebSocket connection
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                    except:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    ws = active_connections[session_key]
                    message = {
                        "type": "llm_update",
                        "call_id": call_id,
                        "data": analysis,
                        "timestamp": datetime.now().isoformat()
                    }
                    # Note: This requires async context, may need refactoring
                    logger.debug(f"Would send to frontend: {message}")
            except Exception as e:
                logger.debug(f"Could not send to frontend: {e}")
        
        # Also publish to Redis pub/sub for frontend subscription
        try:
            channel = f"llm_updates:{call_id}"
            self.redis_client.publish(
                channel,
                json.dumps({
                    "type": "llm_update",
                    "call_id": call_id,
                    "data": analysis,
                    "timestamp": datetime.now().isoformat()
                })
            )
        except Exception as e:
            logger.error(f"Error publishing to Redis: {e}")
    
    def _update_database(self, call_id: str, analysis: Dict, chunks: List[Dict]):
        """Update database with LLM summary."""
        try:
            db = SessionLocal()
            try:
                # Update the most recent chunk with LLM summary
                if chunks:
                    latest_chunk_index = max(ch.get('chunk_index', 0) for ch in chunks)
                    
                    transcript = db.query(MeetingTranscript).filter(
                        MeetingTranscript.call_id == uuid.UUID(call_id),
                        MeetingTranscript.chunk_index == latest_chunk_index
                    ).first()
                    
                    if transcript:
                        transcript.llm_summary = analysis
                        transcript.updated_at = datetime.now()
                        db.commit()
                        logger.debug(f"Updated database with LLM summary for chunk {latest_chunk_index}")
                    else:
                        logger.warning(f"Chunk {latest_chunk_index} not found in database for call {call_id}")
                
            except Exception as e:
                logger.error(f"Error updating database: {e}", exc_info=True)
                db.rollback()
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Database update error: {e}", exc_info=True)
    
    def run(self, batch_size: int = 10, block_ms: int = 1000):
        """
        Main processing loop.
        
        Args:
            batch_size: Number of messages to process per batch
            block_ms: Block time in milliseconds when waiting for messages
        """
        logger.info(f"🚀 Starting LLM processor (consumer: {self.consumer_name})")
        logger.info(f"Consuming from stream: {self.stream_name}")
        logger.info(f"Analysis interval: {self.llm_analyzer.analysis_interval}s")
        logger.info(f"Context window: {self.llm_analyzer.max_context_chunks} chunks")
        
        while True:
            try:
                # Read messages from stream
                messages = self.redis_client.xreadgroup(
                    groupname=self.consumer_group,
                    consumername=self.consumer_name,
                    streams={self.stream_name: '>'},
                    count=batch_size,
                    block=block_ms
                )
                
                if not messages:
                    # Periodic analysis for active calls
                    self._periodic_analysis()
                    continue
                
                # Process each message
                stream_name, stream_messages = messages[0]
                
                for message_id, message_data in stream_messages:
                    success = self.process_chunk(message_id, message_data)
                    
                    if success:
                        # Acknowledge message
                        self.redis_client.xack(
                            self.stream_name,
                            self.consumer_group,
                            message_id
                        )
                    else:
                        logger.warning(f"Failed to process message {message_id}, will retry")
                
            except redis.exceptions.ConnectionError as e:
                logger.error(f"Redis connection error: {e}")
                logger.info("Retrying in 5 seconds...")
                time.sleep(5)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in processing loop: {e}", exc_info=True)
                time.sleep(1)
    
    def _periodic_analysis(self):
        """Perform periodic analysis on active calls."""
        current_time = time.time()
        for call_id, last_time in list(self.last_analysis_time.items()):
            time_since_last = current_time - last_time
            if time_since_last >= self.llm_analyzer.analysis_interval * 2:
                # Re-analyze if enough time has passed
                if self.transcript_buffers.get(call_id):
                    self._analyze_and_update(call_id)


def main():
    """Main entry point."""
    processor = LLMProcessor()
    
    try:
        processor.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        logger.info("LLM Processor shutdown complete")


if __name__ == "__main__":
    main()
