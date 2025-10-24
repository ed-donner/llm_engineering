"""
LLM Engine for local inference and streaming.
Supports Ollama and llama.cpp adapters with token streaming capabilities.
Implements the exact streaming protocol specified in the LLD.
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator, Dict, List, Optional, Any, Union
import aiohttp
import httpx

from .settings import get_settings
from .diagnostics import get_logger
from .retrieval import RetrievalResult
from .storage import get_document_storage

logger = get_logger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"


@dataclass
class LLMConfig:
    """LLM configuration parameters"""
    model_name: str
    provider: LLMProvider = LLMProvider.OLLAMA
    max_tokens: int = 2048
    temperature: float = 0.1
    top_p: float = 0.9
    stop_sequences: List[str] = None
    context_window: int = 8192
    
    def __post_init__(self):
        if self.stop_sequences is None:
            self.stop_sequences = []


@dataclass
class GenerationRequest:
    """Request for LLM generation"""
    prompt: str
    retrieval_result: Optional[RetrievalResult] = None
    config: Optional[LLMConfig] = None
    stream: bool = True
    include_citations: bool = True


@dataclass
class StreamToken:
    """Single streaming token"""
    text: str
    is_final: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GenerationResult:
    """Complete generation result"""
    text: str
    tokens_generated: int
    generation_time: float
    model_info: Dict[str, Any]
    citations: List[Dict[str, Any]]
    stop_reason: str


class LLMEngine(ABC):
    """Abstract base class for LLM engines"""
    
    @abstractmethod
    async def generate_stream(
        self, 
        request: GenerationRequest,
        conversation_context: str = ""
    ) -> AsyncGenerator[StreamToken, None]:
        """Generate streaming response"""
        pass
    
    @abstractmethod
    async def generate(self, request: GenerationRequest, conversation_context: str = "") -> GenerationResult:
        """Generate complete response"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM service is available"""
        pass
    
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        pass


class OllamaEngine(LLMEngine):
    """Ollama LLM engine implementation"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.settings = get_settings()
        self.base_url = self.settings.ollama_host.rstrip('/')
        self.session: Optional[httpx.AsyncClient] = None
        
    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session"""
        if self.session is None:
            self.session = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0),  # Extended to 120 seconds for complex ML queries
                limits=httpx.Limits(max_connections=10)
            )
        return self.session
    
    async def _build_prompt(self, request: GenerationRequest, conversation_context: str = "") -> str:
        """Build the complete prompt with context and citations"""
        prompt_parts = []
        
        # System prompt
        system_prompt = """You are a helpful AI assistant that answers questions based STRICTLY on the provided context. 

CRITICAL RULES - FOLLOW EXACTLY:
1. ONLY use information explicitly stated in the provided context below
2. If the context doesn't contain the answer, say "I don't have that information in the provided context"
3. DO NOT make assumptions, infer, or add information not in the context
4. DO NOT use your general knowledge - stick to what's provided
5. Be accurate and concise - cite specific details from the context
6. If you're uncertain, say so clearly

FORMATTING REQUIREMENTS:
- Use proper markdown formatting in all responses
- Use **bold** for emphasis and important terms
- Use bullet points with - or * for lists
- Use numbered lists when appropriate (1., 2., 3.)
- Use ## for section headers when organizing long responses
- Use `code` formatting for technical terms, filenames, or code snippets
- Use > for quotes or important callouts when relevant

MATHEMATICAL NOTATION:
- Use LaTeX notation for mathematical expressions
- For inline math, use single dollar signs: $P_{11} = 0.7$
- For display math (block equations), use double dollar signs: $$P = \begin{pmatrix} 0.7 & 0.3 \\ 0.4 & 0.6 \end{pmatrix}$$
- Use proper LaTeX syntax for matrices, fractions, subscripts, superscripts, etc.
- Mathematical expressions will be rendered beautifully with KaTeX

CONTEXT AWARENESS:
- When asked "how many documents do you have as context?":
  * Count ONLY the actual uploaded PDF/document files in the system
  * DO NOT count academic references, citations, or bibliography entries within documents
  * A single PDF containing 100 citations still counts as 1 document
  * Answer with the exact number of source files uploaded to the system
- If there is previous conversation context, use it to understand references like "it", "they", "this", etc.

IMPORTANT: Do not include chunk references, citations, or source numbers in your responses. Simply answer based on the provided information without referencing specific chunks or document sections."""
        
        prompt_parts.append(f"System: {system_prompt}\n")
        
        # Add conversation context if available
        if conversation_context:
            prompt_parts.append(f"\n{conversation_context}\n")

        # Always include an accurate Uploaded Document Inventory from storage
        try:
            storage = get_document_storage()
            uploaded_docs = await storage.list_documents()
        except Exception as e:
            logger.warning(f"Failed to list uploaded documents: {e}")
            uploaded_docs = []

        # Build a quick lookup from doc_id -> display name
        doc_id_to_display_name = {}
        try:
            for doc in uploaded_docs:
                doc_id = getattr(doc, "id", None)
                # Prefer explicit name fields; fallback to filename-like fields
                display_name = (
                    getattr(doc, "name", None)
                    or getattr(doc, "filename", None)
                    or getattr(doc, "title", None)
                )
                if doc_id and display_name:
                    doc_id_to_display_name[doc_id] = display_name
        except Exception as e:
            logger.warning(f"Failed to build document name map: {e}")

        prompt_parts.append("\n=== UPLOADED DOCUMENT INVENTORY ===\n")
        prompt_parts.append(f"Total uploaded documents in system: {len(uploaded_docs)}\n")
        if uploaded_docs:
            prompt_parts.append("Document files by name:\n")
            for i, doc in enumerate(uploaded_docs, 1):
                name = getattr(doc, "name", None) or getattr(doc, "filename", None) or "Unknown file"
                prompt_parts.append(f"  {i}. \"{name}\"\n")
        prompt_parts.append("\n")
        
        # Add retrieved context if available
        if request.retrieval_result and request.retrieval_result.chunks:
            # Group chunks by document
            from collections import defaultdict
            chunks_by_doc = defaultdict(list)
            
            # Group chunks by document using doc_id first, we'll resolve names after
            for chunk in request.retrieval_result.chunks:
                chunks_by_doc[chunk.doc_id].append(chunk)
            
            # Convert doc_ids to readable names if possible
            doc_id_to_name = {}
            for doc_id in chunks_by_doc.keys():
                # Try to extract filename from common document metadata patterns
                sample_chunk = chunks_by_doc[doc_id][0]
                
                # Look for filename in metadata
                if 'filename' in sample_chunk.metadata:
                    doc_id_to_name[doc_id] = sample_chunk.metadata['filename']
                elif 'document_name' in sample_chunk.metadata:
                    doc_id_to_name[doc_id] = sample_chunk.metadata['document_name']
                elif 'name' in sample_chunk.metadata:
                    doc_id_to_name[doc_id] = sample_chunk.metadata['name']
                elif 'title' in sample_chunk.metadata:
                    doc_id_to_name[doc_id] = sample_chunk.metadata['title']
                else:
                    # Fallback: use uploaded document inventory mapping
                    if doc_id in doc_id_to_display_name:
                        doc_id_to_name[doc_id] = doc_id_to_display_name[doc_id]
                    else:
                        doc_id_to_name[doc_id] = f"Document ID: {doc_id}"
            
            # Regroup with readable names
            final_chunks_by_doc = defaultdict(list)
            for doc_id, chunks in chunks_by_doc.items():
                readable_name = doc_id_to_name[doc_id]
                final_chunks_by_doc[readable_name] = chunks
            
            chunks_by_doc = final_chunks_by_doc
            
            # Now include the context retrieved for this specific answer
            prompt_parts.append("Context from retrieved documents:\n")
            
            # If all chunks are from the same document, present it more clearly
            if len(chunks_by_doc) == 1:
                doc_name, chunks = next(iter(chunks_by_doc.items()))
                prompt_parts.append(f"\n=== RETRIEVED FROM: \"{doc_name}\" ===\n")
                prompt_parts.append("This response includes content from 1 uploaded document file:\n\n")

                for chunk in chunks:
                    prompt_parts.append(f"{chunk.text}\n\n")

                prompt_parts.append("Note: Academic references mentioned within the text are not separate uploaded documents.\n\n")
            else:
                # Multiple documents retrieved for this answer - show them clearly separated
                prompt_parts.append(f"Retrieved content from {len(chunks_by_doc)} uploaded document file(s):\n\n")

                for doc_num, (doc_name, chunks) in enumerate(chunks_by_doc.items(), 1):
                    prompt_parts.append(f"\n=== RETRIEVED DOCUMENT #{doc_num}: \"{doc_name}\" ===\n")
                    prompt_parts.append(f"Relevant content from document #{doc_num}:\n\n")
                    
                    for chunk in chunks:
                        prompt_parts.append(f"{chunk.text}\n\n")

                prompt_parts.append("Retrieved documents in this response:\n")
                for i, doc_name in enumerate(chunks_by_doc.keys(), 1):
                    prompt_parts.append(f"  {i}. \"{doc_name}\"\n")
                prompt_parts.append("Note: Academic references mentioned within these files are NOT separate uploaded documents.\n\n")
        
        # Add the user query
        prompt_parts.append(f"Human: {request.prompt}\n\nAssistant: ")
        
        return "".join(prompt_parts)
    
    async def generate_stream(
        self, 
        request: GenerationRequest,
        conversation_context: str = ""
    ) -> AsyncGenerator[StreamToken, None]:
        """Generate streaming response via Ollama"""
        session = await self._get_session()
        
        # Build the full prompt
        full_prompt = await self._build_prompt(request, conversation_context)
        
        # Prepare Ollama request
        ollama_request = {
            "model": self.config.model_name,
            "prompt": full_prompt,
            "stream": True,
            "options": {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "num_predict": self.config.max_tokens,
            }
        }
        
        # Add stop sequences if provided
        if self.config.stop_sequences:
            ollama_request["options"]["stop"] = self.config.stop_sequences
        
        try:
            logger.info(f"Starting streaming generation with model: {self.config.model_name}")
            
            async with session.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=ollama_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(f"Ollama API error: {response.status_code} - {error_text}")
                
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    try:
                        chunk = json.loads(line)
                        
                        # Extract token text
                        if "response" in chunk:
                            token_text = chunk["response"]
                            if token_text:  # Only yield non-empty tokens
                                yield StreamToken(
                                    text=token_text,
                                    is_final=chunk.get("done", False),
                                    metadata={
                                        "model": chunk.get("model"),
                                        "created_at": chunk.get("created_at")
                                    }
                                )
                        
                        # Check for completion
                        if chunk.get("done", False):
                            logger.info("Streaming generation completed")
                            break
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse Ollama response chunk: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            yield StreamToken(
                text=f"Error generating response: {str(e)}",
                is_final=True,
                metadata={"error": True}
            )
    
    async def generate(self, request: GenerationRequest, conversation_context: str = "") -> GenerationResult:
        """Generate complete response via Ollama"""
        session = await self._get_session()
        
        # Build the full prompt
        full_prompt = await self._build_prompt(request, conversation_context)
        
        # Prepare Ollama request (non-streaming)
        ollama_request = {
            "model": self.config.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "num_predict": self.config.max_tokens,
            }
        }
        
        # Add stop sequences if provided
        if self.config.stop_sequences:
            ollama_request["options"]["stop"] = self.config.stop_sequences
        
        start_time = time.time()
        
        try:
            logger.info(f"Starting non-streaming generation with model: {self.config.model_name}")
            
            response = await session.post(
                f"{self.base_url}/api/generate",
                json=ollama_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            generation_time = time.time() - start_time
            
            # Extract citations from retrieval result
            citations = []
            if request.retrieval_result and request.include_citations:
                for i, chunk in enumerate(request.retrieval_result.chunks, 1):
                    citations.append({
                        "label": i,
                        "doc_id": chunk.doc_id,
                        "chunk_id": chunk.chunk_id,
                        "score": chunk.score,
                        "text_preview": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
                    })
            
            return GenerationResult(
                text=result.get("response", ""),
                tokens_generated=result.get("eval_count", 0),
                generation_time=generation_time,
                model_info={
                    "model": result.get("model"),
                    "created_at": result.get("created_at"),
                    "total_duration": result.get("total_duration"),
                    "load_duration": result.get("load_duration"),
                    "prompt_eval_count": result.get("prompt_eval_count"),
                    "eval_count": result.get("eval_count"),
                    "eval_duration": result.get("eval_duration")
                },
                citations=citations,
                stop_reason=result.get("done_reason", "completed")
            )
            
        except Exception as e:
            logger.error(f"Error in generation: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if Ollama is available"""
        try:
            session = await self._get_session()
            response = await session.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        try:
            session = await self._get_session()
            response = await session.post(
                f"{self.base_url}/api/show",
                json={"name": self.config.model_name}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Model info unavailable: {response.status_code}"}
        
        except Exception as e:
            logger.warning(f"Failed to get model info: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.aclose()
            self.session = None


class LlamaCppEngine(LLMEngine):
    """llama.cpp engine implementation (placeholder for future)"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        logger.warning("LlamaCppEngine is not yet implemented")
    
    async def generate_stream(
        self, 
        request: GenerationRequest,
        conversation_context: str = ""
    ) -> AsyncGenerator[StreamToken, None]:
        """Generate streaming response via llama.cpp"""
        # TODO: Implement llama.cpp streaming
        yield StreamToken(
            text="LlamaCppEngine streaming not yet implemented",
            is_final=True,
            metadata={"error": True}
        )
    
    async def generate(self, request: GenerationRequest, conversation_context: str = "") -> GenerationResult:
        """Generate complete response via llama.cpp"""
        # TODO: Implement llama.cpp generation
        raise NotImplementedError("LlamaCppEngine not yet implemented")
    
    async def health_check(self) -> bool:
        """Check if llama.cpp is available"""
        return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {"error": "LlamaCppEngine not yet implemented"}


class LLMService:
    """High-level LLM service for managing engines"""
    
    def __init__(self):
        self.settings = get_settings()
        self.engine: Optional[LLMEngine] = None
        self.config: Optional[LLMConfig] = None
    
    async def initialize(self, provider: LLMProvider = LLMProvider.OLLAMA) -> bool:
        """Initialize the LLM service with the specified provider"""
        try:
            # Create configuration based on settings and provider
            if provider == LLMProvider.OLLAMA:
                self.config = LLMConfig(
                    model_name=self.settings.llm_model,
                    provider=provider,
                    max_tokens=min(2048, self.settings.max_context_tokens // 2),
                    temperature=0.1,
                    top_p=0.9,
                    context_window=self.settings.max_context_tokens
                )
                self.engine = OllamaEngine(self.config)
                
            elif provider == LLMProvider.LLAMA_CPP:
                self.config = LLMConfig(
                    model_name=self.settings.llm_model,
                    provider=provider,
                    max_tokens=min(2048, self.settings.max_context_tokens // 2),
                    temperature=0.1,
                    top_p=0.9,
                    context_window=self.settings.max_context_tokens
                )
                self.engine = LlamaCppEngine(self.config)
            
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")
            
            # Test the connection
            is_healthy = await self.engine.health_check()
            if not is_healthy:
                logger.warning(f"LLM engine {provider} is not healthy")
                return False
            
            logger.info(f"LLM service initialized with {provider} and model {self.config.model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            return False
    
    async def generate_stream(
        self,
        query: str,
        retrieval_result: Optional[RetrievalResult] = None,
        **kwargs
    ) -> AsyncGenerator[StreamToken, None]:
        """Generate streaming response"""
        if not self.engine:
            raise RuntimeError("LLM service not initialized")
        
        request = GenerationRequest(
            prompt=query,
            retrieval_result=retrieval_result,
            config=self.config,
            stream=True,
            include_citations=kwargs.get('include_citations', True)
        )
        
        async for token in self.engine.generate_stream(request):
            yield token
    
    async def generate(
        self,
        query: str,
        retrieval_result: Optional[RetrievalResult] = None,
        conversation_context: str = "",
        **kwargs
    ) -> GenerationResult:
        """Generate complete response"""
        if not self.engine:
            raise RuntimeError("LLM service not initialized")

        request = GenerationRequest(
            prompt=query,
            retrieval_result=retrieval_result,
            config=self.config,
            stream=False,
            include_citations=kwargs.get('include_citations', True)
        )
        
        return await self.engine.generate(request, conversation_context)

    async def generate_stream(
        self,
        query: str,
        retrieval_result: Optional[RetrievalResult] = None,
        conversation_context: str = "",
        **kwargs
    ) -> AsyncGenerator[StreamToken, None]:
        """Generate streaming response"""
        if not self.engine:
            raise RuntimeError("LLM service not initialized")

        request = GenerationRequest(
            prompt=query,
            retrieval_result=retrieval_result,
            config=self.config,
            stream=True,
            include_citations=kwargs.get('include_citations', True)
        )
        
        async for token in self.engine.generate_stream(request, conversation_context):
            yield token
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        if not self.engine:
            return {
                "healthy": False,
                "error": "LLM service not initialized"
            }
        
        is_healthy = await self.engine.health_check()
        model_info = await self.engine.get_model_info()
        
        return {
            "healthy": is_healthy,
            "provider": self.config.provider.value,
            "model": self.config.model_name,
            "model_info": model_info
        }
    
    async def close(self):
        """Close the LLM service"""
        if self.engine and hasattr(self.engine, 'close'):
            await self.engine.close()
        self.engine = None
        self.config = None


# Global LLM service instance
_llm_service: Optional[LLMService] = None


async def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance"""
    global _llm_service
    
    if _llm_service is None:
        _llm_service = LLMService()
        
        # Try to initialize with Ollama first
        if not await _llm_service.initialize(LLMProvider.OLLAMA):
            logger.warning("Failed to initialize with Ollama, trying llama.cpp")
            if not await _llm_service.initialize(LLMProvider.LLAMA_CPP):
                logger.error("Failed to initialize any LLM provider")
                raise RuntimeError("No LLM provider available")
    
    return _llm_service


async def test_llm_generation(query: str = "What is machine learning?") -> Dict[str, Any]:
    """Test function for LLM generation"""
    try:
        llm_service = await get_llm_service()
        
        # Test complete generation
        start_time = time.time()
        result = await llm_service.generate(query)
        generation_time = time.time() - start_time
        
        return {
            "success": True,
            "query": query,
            "response": result.text,
            "tokens_generated": result.tokens_generated,
            "generation_time": generation_time,
            "model_info": result.model_info
        }
        
    except Exception as e:
        logger.error(f"LLM generation test failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Export key classes and functions
__all__ = [
    "LLMService",
    "LLMConfig", 
    "GenerationRequest",
    "GenerationResult",
    "StreamToken",
    "LLMProvider",
    "get_llm_service",
    "test_llm_generation"
]
