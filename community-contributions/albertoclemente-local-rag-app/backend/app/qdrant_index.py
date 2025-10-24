"""
Qdrant vector database integration for RAG chunk storage and retrieval.

This module provides:
- Collection management (create, configure, delete)
- Vector indexing with payload metadata
- Similarity search with filters
- Batch operations for performance
- Health monitoring and diagnostics
"""

import asyncio
import functools
import logging
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

import numpy as np

from .settings import get_settings
from .diagnostics import get_logger

# Optional dependency - graceful degradation
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import (
        Distance, VectorParams, CreateCollection, PointStruct,
        Filter, FieldCondition, Match, MatchAny, MatchValue, SearchRequest, CountRequest,
        CollectionInfo, UpdateStatus
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QdrantClient = None
    models = None
    Distance = None
    VectorParams = None
    CreateCollection = None
    PointStruct = None
    Filter = None
    FieldCondition = None
    Match = None
    SearchRequest = None
    CountRequest = None
    CollectionInfo = None
    UpdateStatus = None
    QDRANT_AVAILABLE = False

logger = get_logger(__name__)

class QdrantConfig:
    """Configuration for Qdrant based on performance profile."""
    
    # Collection configurations by performance profile
    COLLECTION_CONFIGS = {
        'eco': {
            'vectors_config': {
                'size': 384,  # all-MiniLM-L6-v2
                'distance': 'Cosine'
            },
            'optimizers_config': {
                'default_segment_number': 2,
                'max_segment_size': 100000,
                'memmap_threshold': 50000,
                'indexing_threshold': 10000,
                'flush_interval_sec': 30
            },
            'hnsw_config': {
                'ef_construct': 100,
                'max_connections': 16
            }
        },
        'balanced': {
            'vectors_config': {
                'size': 768,  # all-mpnet-base-v2
                'distance': 'Cosine'
            },
            'optimizers_config': {
                'default_segment_number': 4,
                'max_segment_size': 200000,
                'memmap_threshold': 100000,
                'indexing_threshold': 20000,
                'flush_interval_sec': 15
            },
            'hnsw_config': {
                'ef_construct': 200,
                'max_connections': 32
            }
        },
        'performance': {
            'vectors_config': {
                'size': 768,  # all-mpnet-base-v2
                'distance': 'Cosine'
            },
            'optimizers_config': {
                'default_segment_number': 8,
                'max_segment_size': 500000,
                'memmap_threshold': 200000,
                'indexing_threshold': 50000,
                'flush_interval_sec': 5
            },
            'hnsw_config': {
                'ef_construct': 400,
                'max_connections': 64
            }
        }
    }
    
    @classmethod
    def get_config(cls, profile: str) -> Dict[str, Any]:
        """Get Qdrant config for performance profile."""
        return cls.COLLECTION_CONFIGS.get(profile, cls.COLLECTION_CONFIGS['balanced'])

class QdrantIndex:
    """Qdrant vector database operations for RAG chunks."""
    
    COLLECTION_NAME = "rag_chunks"
    
    def __init__(self, profile: str = 'balanced'):
        self.profile = profile
        self.config = QdrantConfig.get_config(profile)
        self.client: Optional[Any] = None
        self.collection_exists = False
        
        # Get Qdrant configuration from settings
        settings = get_settings()
        self.qdrant_url = getattr(settings, 'qdrant_url', 'http://localhost:6333')
        self.qdrant_path = getattr(settings, 'qdrant_path', None)
        
        # If no explicit path set, use data directory
        if self.qdrant_path is None:
            self.qdrant_path = settings.qdrant_data_dir
        
        logger.info(f"Initialized QdrantIndex with profile={profile}, url={self.qdrant_url}, path={self.qdrant_path}")
    
    async def initialize(self) -> None:
        """Initialize Qdrant client and ensure collection exists."""
        if self.client is not None:
            return
        
        if not QDRANT_AVAILABLE:
            raise RuntimeError(
                "qdrant-client not available. Install with: pip install qdrant-client"
            )
        
        logger.info(f"Connecting to Qdrant at {self.qdrant_url}")
        
        try:
            # Skip server mode and go directly to file-based for reliability
            logger.info(f"Using file-based Qdrant at {self.qdrant_path}")
            
            # Create data directory if it doesn't exist
            Path(self.qdrant_path).mkdir(parents=True, exist_ok=True)
            
            # Create local file-based client
            self.client = QdrantClient(path=self.qdrant_path)
            logger.info(f"✅ Using file-based Qdrant at {self.qdrant_path}")
            
            # Ensure collection exists
            await self._ensure_collection()
            
            logger.info("Qdrant client initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Qdrant client: {e}")
            self.client = None
            raise
    
    async def _test_connection(self) -> None:
        """Test Qdrant connection."""
        if self.client is None:
            raise RuntimeError("Client not initialized")
        
        loop = asyncio.get_event_loop()
        
        try:
            # For file-based Qdrant, test with get_collections instead
            if hasattr(self.client, '_client') and hasattr(self.client._client, 'grpc_client'):
                # Server-based client
                await loop.run_in_executor(None, self.client.get_cluster_info)
            else:
                # File-based client - just test basic operation
                await loop.run_in_executor(None, self.client.get_collections)
        except Exception as e:
            raise RuntimeError(f"Cannot connect to Qdrant at {self.qdrant_url}: {e}")
    
    async def _ensure_collection(self) -> None:
        """Ensure the rag_chunks collection exists with proper configuration."""
        if self.client is None:
            raise RuntimeError("Client not initialized")
        
        loop = asyncio.get_event_loop()
        
        try:
            # Check if collection exists
            collections = await loop.run_in_executor(None, self.client.get_collections)
            collection_names = [c.name for c in collections.collections]
            
            if self.COLLECTION_NAME in collection_names:
                logger.info(f"Collection {self.COLLECTION_NAME} already exists")
                self.collection_exists = True
                
                # Verify collection configuration
                await self._verify_collection_config()
                return
            
            # Create collection
            logger.info(f"Creating collection {self.COLLECTION_NAME}")
            
            vectors_config = VectorParams(
                size=self.config['vectors_config']['size'],
                distance=getattr(Distance, self.config['vectors_config']['distance'].upper())
            )
            
            await loop.run_in_executor(
                None,
                self.client.create_collection,
                self.COLLECTION_NAME,
                vectors_config
            )
            
            # Update collection settings for performance
            await self._update_collection_settings()
            
            self.collection_exists = True
            logger.info(f"Collection {self.COLLECTION_NAME} created successfully")
            
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise
    
    async def _verify_collection_config(self) -> None:
        """Verify that collection has the expected configuration."""
        if self.client is None:
            raise RuntimeError("Client not initialized")
        
        loop = asyncio.get_event_loop()
        
        try:
            collection_info = await loop.run_in_executor(
                None,
                self.client.get_collection,
                self.COLLECTION_NAME
            )
            
            # Check vector size
            expected_size = self.config['vectors_config']['size']
            actual_size = collection_info.config.params.vectors.size
            
            if actual_size != expected_size:
                logger.warning(
                    f"Collection vector size mismatch: expected {expected_size}, "
                    f"got {actual_size}. Consider recreating collection."
                )
            
        except Exception as e:
            logger.warning(f"Error verifying collection config: {e}")
    
    async def _update_collection_settings(self) -> None:
        """Update collection settings for optimal performance."""
        if self.client is None:
            raise RuntimeError("Client not initialized")
        
        loop = asyncio.get_event_loop()
        
        try:
            # Update optimizer settings
            optimizer_config = models.OptimizersConfigDiff(
                **self.config['optimizers_config']
            )
            
            await loop.run_in_executor(
                None,
                self.client.update_collection,
                self.COLLECTION_NAME,
                optimizer_config=optimizer_config
            )
            
            # Update HNSW settings
            hnsw_config = models.HnswConfigDiff(
                **self.config['hnsw_config']
            )
            
            await loop.run_in_executor(
                None,
                self.client.update_collection,
                self.COLLECTION_NAME,
                hnsw_config=hnsw_config
            )
            
            logger.info("Collection settings updated for optimal performance")
            
        except Exception as e:
            logger.warning(f"Error updating collection settings: {e}")
    
    async def index_chunks(self, chunks: List[Dict[str, Any]], doc_id: str) -> Dict[str, Any]:
        """
        Index chunks with embeddings into Qdrant.
        
        Args:
            chunks: List of chunks with embeddings and metadata
            doc_id: Document ID for filtering
        
        Returns:
            Dictionary with indexing statistics
        """
        await self.initialize()
        
        if not chunks:
            return {'indexed': 0, 'skipped': 0, 'errors': 0}
        
        logger.info(f"Indexing {len(chunks)} chunks for document {doc_id}")
        start_time = time.time()
        
        points = []
        stats = {'indexed': 0, 'skipped': 0, 'errors': 0}
        
        for i, chunk in enumerate(chunks):
            try:
                # Validate chunk data
                if 'embedding' not in chunk:
                    logger.warning(f"Chunk {i} missing embedding, skipping")
                    stats['skipped'] += 1
                    continue
                
                if 'text' not in chunk:
                    logger.warning(f"Chunk {i} missing text, skipping")
                    stats['skipped'] += 1
                    continue
                
                # Create point with UUID
                # Use deterministic UUID based on doc_id and chunk_id for consistency
                import hashlib
                point_key = f"{doc_id}_{chunk.get('chunk_id', i)}"
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, point_key))
                
                # Prepare payload with metadata
                payload = {
                    'doc_id': doc_id,
                    'chunk_id': chunk.get('chunk_id', i),
                    'text': chunk['text'],
                    'chunk_index': i,
                    'token_count': chunk.get('token_count', 0),
                    'char_count': len(chunk['text']),
                    'indexed_at': time.time()
                }
                
                # Add optional metadata
                if 'metadata' in chunk:
                    for key, value in chunk['metadata'].items():
                        if key not in payload and isinstance(value, (str, int, float, bool)):
                            payload[f"meta_{key}"] = value
                
                # Create point
                if isinstance(chunk['embedding'], np.ndarray):
                    vector_data = chunk['embedding'].tolist()
                else:
                    vector_data = chunk['embedding']
                
                logger.info(f"Creating point {point_id} with vector type: {type(vector_data)}, shape: {len(vector_data) if isinstance(vector_data, list) else 'unknown'}")
                
                point = PointStruct(
                    id=point_id,
                    vector=vector_data,
                    payload=payload
                )
                
                points.append(point)
                stats['indexed'] += 1
                
            except Exception as e:
                logger.error(f"Error preparing chunk {i} for indexing: {e}")
                stats['errors'] += 1
        
        # Batch insert points
        if points:
            try:
                logger.info(f"Upserting {len(points)} points. First point vector type: {type(points[0].vector) if points else 'none'}")
                loop = asyncio.get_event_loop()
                operation_info = await loop.run_in_executor(
                    None,
                    self.client.upsert,
                    self.COLLECTION_NAME,
                    points
                )
                logger.info(f"Upsert operation result: {operation_info}")
                
                # Wait for operation to complete
                if hasattr(operation_info, 'operation_id'):
                    await self._wait_for_operation(operation_info.operation_id)
                
                index_time = time.time() - start_time
                logger.info(
                    f"Indexed {len(points)} points for document {doc_id} in {index_time:.2f}s"
                )
                
            except Exception as e:
                logger.error(f"Error indexing chunks: {e}")
                stats['errors'] += len(points)
                stats['indexed'] = 0
        
        return stats
    
    async def search_similar(
        self,
        query_embedding: np.ndarray,
        limit: int = 10,
        doc_filter: Optional[List[str]] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Query vector
            limit: Maximum number of results
            doc_filter: List of document IDs to filter by
            score_threshold: Minimum similarity score
        
        Returns:
            List of similar chunks with scores and metadata
        """
        await self.initialize()
        
        # Convert numpy array to list
        if isinstance(query_embedding, np.ndarray):
            query_vector = query_embedding.tolist()
        else:
            query_vector = query_embedding
        
        # Build filter
        query_filter = None
        if doc_filter:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchAny(any=doc_filter)
                    )
                ]
            )
        
        try:
            loop = asyncio.get_event_loop()
            search_result = await loop.run_in_executor(
                None,
                lambda: self.client.search(
                    collection_name=self.COLLECTION_NAME,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=limit,
                    score_threshold=score_threshold
                )
            )
            
            # Convert results to our format
            results = []
            for scored_point in search_result:
                result = {
                    'id': scored_point.id,
                    'score': scored_point.score,
                    'doc_id': scored_point.payload.get('doc_id'),
                    'chunk_id': scored_point.payload.get('chunk_id'),
                    'text': scored_point.payload.get('text', ''),
                    'token_count': scored_point.payload.get('token_count', 0),
                    'chunk_index': scored_point.payload.get('chunk_index', 0),
                    'metadata': {}
                }
                
                # Extract metadata fields
                for key, value in scored_point.payload.items():
                    if key.startswith('meta_'):
                        result['metadata'][key[5:]] = value
                
                results.append(result)
            
            logger.debug(f"Found {len(results)} similar chunks")
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {e}")
            return []
    
    async def delete_document_chunks(self, doc_id: str) -> int:
        """
        Delete all chunks for a document.
        
        Args:
            doc_id: Document ID
        
        Returns:
            Number of chunks deleted
        """
        await self.initialize()
        
        logger.info(f"Deleting chunks for document {doc_id}")
        
        try:
            # Create filter for document
            doc_filter = Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=doc_id)
                    )
                ]
            )
            
            loop = asyncio.get_event_loop()
            delete_func = functools.partial(
                self.client.delete,
                self.COLLECTION_NAME,
                points_selector=models.FilterSelector(filter=doc_filter)
            )
            operation_info = await loop.run_in_executor(None, delete_func)
            
            # Wait for operation to complete
            if hasattr(operation_info, 'operation_id'):
                await self._wait_for_operation(operation_info.operation_id)
            
            # Count deleted (approximate)
            # Note: Qdrant doesn't return exact count, so we estimate
            logger.info(f"Deleted chunks for document {doc_id}")
            return 1  # Return success indicator
            
        except Exception as e:
            logger.error(f"Error deleting chunks for document {doc_id}: {e}")
            return 0
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        await self.initialize()
        
        try:
            loop = asyncio.get_event_loop()
            
            # Get collection info
            collection_info = await loop.run_in_executor(
                None,
                self.client.get_collection,
                self.COLLECTION_NAME
            )
            
            stats = {
                'collection_name': self.COLLECTION_NAME,
                'points_count': collection_info.points_count,
                'segments_count': collection_info.segments_count,
                'vector_size': collection_info.config.params.vectors.size,
                'distance': collection_info.config.params.vectors.distance.name,
                'status': collection_info.status.name,
                'optimizer': collection_info.config.optimizer_config.dict() if collection_info.config.optimizer_config else {},
                'profile': self.profile
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {
                'collection_name': self.COLLECTION_NAME,
                'error': str(e),
                'available': False
            }

    async def get_document_chunk_count(self, doc_id: str) -> int:
        """Get the number of chunks for a specific document"""
        if self.client is None:
            return 0
        
        await self.initialize()
        loop = asyncio.get_event_loop()
        
        try:
            # Simple approach: get all points and count manually
            # This avoids complex filter instantiation issues
            search_results = await loop.run_in_executor(
                None,
                lambda: self.client.scroll(
                    collection_name=self.COLLECTION_NAME,
                    limit=10000,  # Large limit to get all chunks
                    with_payload=True,  # Need payload to check doc_id
                    with_vectors=False
                )
            )
            
            points, _ = search_results
            
            # Count points that match our document ID
            count = 0
            for point in points:
                if hasattr(point, 'payload') and point.payload and point.payload.get('doc_id') == doc_id:
                    count += 1
            
            return count
                
        except Exception as e:
            logger.error(f"Error counting chunks for document {doc_id}: {e}")
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Qdrant health status."""
        try:
            await self.initialize()
            
            loop = asyncio.get_event_loop()
            
            try:
                # Try to get cluster info (server mode)
                cluster_info = await loop.run_in_executor(None, self.client.get_cluster_info)
                return {
                    'status': 'healthy',
                    'mode': 'server',
                    'peer_id': cluster_info.peer_id,
                    'raft_info': cluster_info.raft_info,
                    'collection_exists': self.collection_exists,
                    'url': self.qdrant_url
                }
            except:
                # File-based mode
                collections = await loop.run_in_executor(None, self.client.get_collections)
                return {
                    'status': 'healthy',
                    'mode': 'local',
                    'collections_count': len(collections.collections),
                    'collection_exists': self.collection_exists,
                    'path': self.qdrant_path
                }
            
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'url': self.qdrant_url,
                'path': self.qdrant_path
            }
    
    async def _wait_for_operation(self, operation_id: int, timeout: float = 30.0) -> bool:
        """Wait for a Qdrant operation to complete."""
        # For file-based Qdrant, operations are synchronous, so we don't need to wait
        if hasattr(self.client, '_client') and hasattr(self.client._client, 'grpc_client'):
            # Server-based client - check operations
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    loop = asyncio.get_event_loop()
                    operations = await loop.run_in_executor(
                        None,
                        self.client.get_operations
                    )
                    
                    # Check if operation is still running
                    for op in operations.operations:
                        if op.operation_id == operation_id:
                            if op.status != UpdateStatus.COMPLETED:
                                await asyncio.sleep(0.1)
                                continue
                            else:
                                return True
                    
                    # Operation not found, assume completed
                    return True
                    
                except Exception as e:
                    logger.warning(f"Error checking operation status: {e}")
                    return True  # Assume completed on error
            
            logger.warning(f"Operation {operation_id} timeout after {timeout}s")
            return False
        else:
            # File-based client - operations are synchronous, so always return True
            return True
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                logger.warning(f"Error closing Qdrant client: {e}")
            finally:
                self.client = None
        
        self.collection_exists = False
        logger.info("Qdrant client cleaned up")

# Global index instance
_index: Optional[QdrantIndex] = None

async def get_qdrant_index(profile: Optional[str] = None) -> QdrantIndex:
    """Get or create the global Qdrant index instance."""
    global _index
    
    settings = get_settings()
    current_profile = profile or settings.performance_profile
    
    # Create new index if needed or profile changed
    if _index is None or _index.profile != current_profile:
        if _index is not None:
            await _index.cleanup()
        
        _index = QdrantIndex(current_profile)
        await _index.initialize()
    
    return _index

# Dependency injection function for FastAPI
async def get_qdrant_service(profile: Optional[str] = None) -> QdrantIndex:
    """FastAPI dependency for Qdrant service."""
    return await get_qdrant_index(profile)
