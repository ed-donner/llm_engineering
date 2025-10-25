"""
Local embedding generation and caching.

This module provides local-only embedding generation using sentence-transformers
or similar models. Features:
- Batch processing for efficiency
- Caching to avoid recomputation
- Multiple model support (based on performance profile)
- GPU fallback with CPU-only mode
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

import numpy as np

from .settings import get_settings
from .diagnostics import get_logger

# Optional dependencies - graceful degradation
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False

logger = get_logger(__name__)

class EmbeddingConfig:
    """Configuration for embedding models based on performance profile."""
    
    # Model configurations by performance profile
    MODEL_CONFIGS = {
        'eco': {
            'model_name': 'all-MiniLM-L6-v2',  # ~80MB, 384 dims
            'device': 'cpu',
            'batch_size': 16,
            'max_workers': 2,
            'normalize_embeddings': True
        },
        'balanced': {
            'model_name': 'all-mpnet-base-v2',  # ~420MB, 768 dims  
            'device': 'auto',  # GPU if available
            'batch_size': 32,
            'max_workers': 4,
            'normalize_embeddings': True
        },
        'performance': {
            'model_name': 'all-mpnet-base-v2',  # Same model, more resources
            'device': 'auto',
            'batch_size': 64,
            'max_workers': 8,
            'normalize_embeddings': True
        }
    }
    
    @classmethod
    def get_config(cls, profile: str) -> Dict[str, Any]:
        """Get embedding config for performance profile."""
        return cls.MODEL_CONFIGS.get(profile, cls.MODEL_CONFIGS['balanced'])

class EmbeddingCache:
    """Simple file-based cache for embeddings."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {'hits': 0, 'misses': 0}
    
    def _text_hash(self, text: str, model_name: str) -> str:
        """Generate hash for text + model combination."""
        content = f"{model_name}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get(self, text: str, model_name: str) -> Optional[np.ndarray]:
        """Get cached embedding if available."""
        cache_key = self._text_hash(text, model_name)
        cache_file = self.cache_dir / f"{cache_key}.npy"
        
        if cache_file.exists():
            try:
                embedding = np.load(cache_file)
                self.stats['hits'] += 1
                return embedding
            except Exception as e:
                logger.warning(f"Error loading cached embedding {cache_key}: {e}")
                cache_file.unlink(missing_ok=True)
        
        self.stats['misses'] += 1
        return None
    
    def set(self, text: str, model_name: str, embedding: np.ndarray) -> None:
        """Cache embedding."""
        cache_key = self._text_hash(text, model_name)
        cache_file = self.cache_dir / f"{cache_key}.npy"
        
        try:
            np.save(cache_file, embedding)
        except Exception as e:
            logger.warning(f"Error caching embedding {cache_key}: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return self.stats.copy()
    
    def clear(self) -> int:
        """Clear cache and return number of files removed."""
        count = 0
        for cache_file in self.cache_dir.glob("*.npy"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Error removing cache file {cache_file}: {e}")
        
        self.stats = {'hits': 0, 'misses': 0}
        return count

class LocalEmbedder:
    """Local embedding generation with caching and batching."""
    
    def __init__(self, profile: str = 'balanced'):
        self.profile = profile
        self.config = EmbeddingConfig.get_config(profile)
        self.model_name = self.config['model_name']
        self.device = self._determine_device()
        self.model: Optional[Any] = None
        self.executor: Optional[ThreadPoolExecutor] = None
        
        # Initialize cache
        settings = get_settings()
        cache_dir = Path(settings.storage_path) / "embeddings_cache"
        self.cache = EmbeddingCache(cache_dir)
        
        logger.info(f"Initialized LocalEmbedder with profile={profile}, model={self.model_name}, device={self.device}")
    
    def _determine_device(self) -> str:
        """Determine the best device to use."""
        device = self.config['device']
        
        if device == 'auto':
            if TORCH_AVAILABLE and torch.cuda.is_available():
                return 'cuda'
            elif TORCH_AVAILABLE and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return 'mps'  # Apple Silicon
            else:
                return 'cpu'
        
        return device
    
    async def initialize(self) -> None:
        """Initialize the embedding model asynchronously."""
        if self.model is not None:
            return
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise RuntimeError(
                "sentence-transformers not available. Install with: pip install sentence-transformers"
            )
        
        logger.info(f"Loading embedding model {self.model_name} on device {self.device}")
        start_time = time.time()
        
        # Load model in thread executor to avoid blocking
        loop = asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=self.config['max_workers'])
        
        try:
            self.model = await loop.run_in_executor(
                self.executor,
                self._load_model
            )
            
            load_time = time.time() - start_time
            logger.info(f"Loaded embedding model in {load_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            if self.executor:
                self.executor.shutdown(wait=False)
            raise
    
    def _load_model(self) -> Any:
        """Load the sentence transformer model."""
        model = SentenceTransformer(self.model_name, device=self.device)
        return model
    
    async def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        embeddings = await self.embed_texts([text])
        embedding = embeddings[0]
        
        # Ensure 1D output for single text
        if embedding.ndim > 1:
            embedding = embedding.squeeze()
        
        return embedding
    
    async def embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts with caching and batching."""
        if not texts:
            return []
        
        await self.initialize()
        
        # Check cache first
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cached_embedding = self.cache.get(text, self.model_name)
            if cached_embedding is not None:
                embeddings.append((i, cached_embedding))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            logger.debug(f"Generating embeddings for {len(uncached_texts)} texts")
            start_time = time.time()
            
            loop = asyncio.get_event_loop()
            new_embeddings = await loop.run_in_executor(
                self.executor,
                self._generate_embeddings,
                uncached_texts
            )
            
            generation_time = time.time() - start_time
            logger.debug(f"Generated {len(new_embeddings)} embeddings in {generation_time:.2f}s")
            
            # Cache new embeddings
            for text, embedding in zip(uncached_texts, new_embeddings):
                self.cache.set(text, self.model_name, embedding)
            
            # Add to results
            for i, embedding in zip(uncached_indices, new_embeddings):
                embeddings.append((i, embedding))
        
        # Sort by original order and return
        embeddings.sort(key=lambda x: x[0])
        return [emb for _, emb in embeddings]
    
    def _generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using the model (runs in thread)."""
        if self.model is None:
            raise RuntimeError("Model not initialized")
        
        batch_size = self.config['batch_size']
        normalize = self.config['normalize_embeddings']
        
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            try:
                batch_embeddings = self.model.encode(
                    batch_texts,
                    normalize_embeddings=normalize,
                    convert_to_numpy=True,
                    show_progress_bar=False
                )
                
                # Ensure consistent shape: always 2D, then extract individual vectors
                if batch_embeddings.ndim == 1:
                    # Single text case - add batch dimension
                    batch_embeddings = batch_embeddings.reshape(1, -1)
                
                # Convert to list of 1D arrays
                batch_embeddings = [batch_embeddings[i] for i in range(batch_embeddings.shape[0])]
                
                all_embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"Error generating embeddings for batch: {e}")
                # Return zero vectors as fallback
                dummy_size = self.get_embedding_dimension()
                dummy_embeddings = [np.zeros(dummy_size) for _ in batch_texts]
                all_embeddings.extend(dummy_embeddings)
        
        return all_embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this model."""
        if self.model_name == 'all-MiniLM-L6-v2':
            return 384
        elif self.model_name == 'all-mpnet-base-v2':
            return 768
        else:
            # Default fallback - will be corrected once model is loaded
            return 768
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        await self.initialize()
        
        info = {
            'model_name': self.model_name,
            'device': self.device,
            'profile': self.profile,
            'dimension': self.get_embedding_dimension(),
            'cache_stats': self.cache.get_stats(),
            'available': SENTENCE_TRANSFORMERS_AVAILABLE
        }
        
        if self.model is not None:
            try:
                info['max_seq_length'] = self.model.max_seq_length
                info['device_used'] = str(self.model.device)
            except Exception:
                pass
        
        return info
    
    async def warm_up(self, sample_texts: Optional[List[str]] = None) -> None:
        """Warm up the model with sample texts."""
        if sample_texts is None:
            sample_texts = [
                "This is a sample text for warming up the embedding model.",
                "Another example to ensure the model is ready for inference."
            ]
        
        logger.info("Warming up embedding model...")
        start_time = time.time()
        
        await self.embed_texts(sample_texts)
        
        warmup_time = time.time() - start_time
        logger.info(f"Model warmed up in {warmup_time:.2f}s")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
        
        self.model = None
        logger.info("Embedding model cleaned up")

# Global embedder instance
_embedder: Optional[LocalEmbedder] = None

async def get_embedder(profile: Optional[str] = None) -> LocalEmbedder:
    """Get or create the global embedder instance."""
    global _embedder
    
    settings = get_settings()
    current_profile = profile or settings.performance_profile
    
    # Create new embedder if needed or profile changed
    if _embedder is None or _embedder.profile != current_profile:
        if _embedder is not None:
            await _embedder.cleanup()
        
        _embedder = LocalEmbedder(current_profile)
        await _embedder.initialize()
    
    return _embedder

async def embed_chunks(chunks: List[Dict[str, Any]], profile: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Embed a list of chunks and return them with embeddings added.
    
    Args:
        chunks: List of chunk dictionaries with 'text' field
        profile: Performance profile (if different from global)
    
    Returns:
        List of chunks with 'embedding' field added
    """
    if not chunks:
        return []
    
    embedder = await get_embedder(profile)
    
    # Extract texts
    texts = [chunk.get('text', '') for chunk in chunks]
    
    # Generate embeddings
    embeddings = await embedder.embed_texts(texts)
    
    # Add embeddings to chunks
    result_chunks = []
    for chunk, embedding in zip(chunks, embeddings):
        result_chunk = chunk.copy()
        result_chunk['embedding'] = embedding.tolist()  # Convert to list for JSON serialization
        result_chunks.append(result_chunk)
    
    return result_chunks

async def embed_query(query: str, profile: Optional[str] = None) -> np.ndarray:
    """
    Embed a single query text.
    
    Args:
        query: Query text to embed
        profile: Performance profile (if different from global)
    
    Returns:
        Query embedding as numpy array
    """
    embedder = await get_embedder(profile)
    return await embedder.embed_text(query)

async def get_embedding_info(profile: Optional[str] = None) -> Dict[str, Any]:
    """Get information about the current embedding setup."""
    try:
        embedder = await get_embedder(profile)
        return await embedder.get_model_info()
    except Exception as e:
        logger.error(f"Error getting embedding info: {e}")
        return {
            'available': False,
            'error': str(e),
            'model_name': 'unknown',
            'dimension': 0
        }

# Dependency injection function for FastAPI
async def get_embedder_service(profile: Optional[str] = None) -> LocalEmbedder:
    """FastAPI dependency for embedder service."""
    return await get_embedder(profile)
