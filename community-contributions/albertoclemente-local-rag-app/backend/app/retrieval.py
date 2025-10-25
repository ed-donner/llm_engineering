"""
Retrieval engine with dynamic-k control for RAG.

This module implements:
- Similarity search with dynamic k selection
- Coverage analysis and budget management
- Optional local reranking
- Marginal relevance scoring
- Query complexity analysis
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

import numpy as np

from .settings import get_settings
from .diagnostics import get_logger
from .embeddings import embed_query, get_embedder_service
from .qdrant_index import get_qdrant_service

logger = get_logger(__name__)

class QueryComplexity(str, Enum):
    """Query complexity levels for dynamic-k selection."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"

@dataclass
class RetrievalParams:
    """Parameters for retrieval configuration."""
    k_min: int = 3
    k_max: int = 10
    # Minimum similarity threshold for chunks (cosine similarity)
    # Balanced at 30% - filters very low relevance while keeping enough context
    score_threshold: float = 0.3
    epsilon_gain: float = 0.05  # Minimum marginal gain to continue
    coverage_threshold: float = 0.85  # Stop when coverage plateaus
    budget_tokens: int = 4000  # Maximum context budget
    rerank: bool = False
    diversity_penalty: float = 0.1  # Penalty for similar chunks

@dataclass
class ChunkResult:
    """Single chunk retrieval result."""
    id: str
    doc_id: str
    chunk_id: str
    text: str
    score: float
    token_count: int
    chunk_index: int
    metadata: Dict[str, Any]
    rerank_score: Optional[float] = None

@dataclass
class RetrievalResult:
    """Complete retrieval result with analysis."""
    chunks: List[ChunkResult]
    k_used: int
    total_tokens: int
    coverage_score: float
    query_complexity: QueryComplexity
    stop_reason: str
    retrieval_time: float
    stats: Dict[str, Any]
    rerank_time: Optional[float] = None

class QueryAnalyzer:
    """Analyzes query complexity to guide dynamic-k selection."""
    
    # Keywords that suggest complex queries requiring more context
    COMPLEX_INDICATORS = {
        'compare', 'contrast', 'analyze', 'relationship', 'difference', 'similarity',
        'comprehensive', 'detailed', 'overview', 'summary', 'explain why',
        'how does', 'what are the implications', 'pros and cons'
    }
    
    SIMPLE_INDICATORS = {
        'what is', 'who is', 'when', 'where', 'define', 'definition'
    }
    
    @classmethod
    def analyze_complexity(cls, query: str) -> QueryComplexity:
        """Analyze query complexity based on content and structure."""
        query_lower = query.lower()
        words = query_lower.split()
        
        # Count complexity indicators
        complex_score = sum(1 for indicator in cls.COMPLEX_INDICATORS 
                          if indicator in query_lower)
        simple_score = sum(1 for indicator in cls.SIMPLE_INDICATORS 
                         if indicator in query_lower)
        
        # Length-based scoring
        if len(words) > 15:
            complex_score += 1
        elif len(words) < 5:
            simple_score += 1
        
        # Question words analysis
        question_words = ['how', 'why', 'what', 'when', 'where', 'who']
        question_count = sum(1 for word in question_words if word in query_lower)
        
        if question_count > 1:
            complex_score += 1
        
        # Punctuation analysis (multiple sentences = complex)
        if query.count('.') > 1 or query.count('?') > 1:
            complex_score += 1
        
        # Decision logic
        if complex_score > simple_score and complex_score >= 1:
            return QueryComplexity.COMPLEX
        elif simple_score > 0 and complex_score == 0:
            return QueryComplexity.SIMPLE
        else:
            return QueryComplexity.MODERATE

class CoverageMeter:
    """Measures semantic coverage of retrieved chunks."""
    
    def __init__(self):
        self.seen_topics: Set[str] = set()
        self.coverage_history: List[float] = []
    
    def calculate_coverage(self, chunks: List[ChunkResult], query_embedding: np.ndarray) -> float:
        """
        Calculate semantic coverage score for current chunk set.
        
        Uses a combination of:
        - Topic diversity (based on chunk embeddings)
        - Query alignment
        - Content overlap detection
        """
        if not chunks:
            return 0.0
        
        # Extract unique topics/concepts from chunks
        chunk_texts = [chunk.text for chunk in chunks]
        
        # Simple coverage based on unique meaningful terms
        all_words = set()
        for text in chunk_texts:
            # Extract meaningful terms (longer than 3 chars, not common words)
            words = [word.lower().strip('.,!?;:"()[]') 
                    for word in text.split() 
                    if len(word) > 3 and word.lower() not in self._get_stop_words()]
            all_words.update(words)
        
        # Coverage grows with unique content but has diminishing returns
        unique_content_score = min(len(all_words) / 50.0, 1.0)  # Normalize to 50 terms
        
        # Diversity penalty for very similar chunks
        if len(chunks) > 1:
            similarity_penalty = self._calculate_similarity_penalty(chunks)
            unique_content_score *= (1 - similarity_penalty)
        
        # Store coverage progression
        self.coverage_history.append(unique_content_score)
        
        return unique_content_score
    
    def _calculate_similarity_penalty(self, chunks: List[ChunkResult]) -> float:
        """Calculate penalty for highly similar chunks."""
        # Simple overlap-based similarity
        total_overlap = 0
        comparisons = 0
        
        for i in range(len(chunks)):
            for j in range(i + 1, len(chunks)):
                words_i = set(chunks[i].text.lower().split())
                words_j = set(chunks[j].text.lower().split())
                
                overlap = len(words_i & words_j) / max(len(words_i | words_j), 1)
                total_overlap += overlap
                comparisons += 1
        
        if comparisons == 0:
            return 0.0
        
        avg_overlap = total_overlap / comparisons
        return min(avg_overlap, 0.5)  # Cap penalty at 50%
    
    def has_coverage_plateaued(self, threshold: float = 0.85) -> bool:
        """Check if coverage has plateaued (diminishing returns)."""
        if len(self.coverage_history) < 3:
            return False
        
        # Check if recent additions provide minimal coverage gain
        recent = self.coverage_history[-3:]
        if len(recent) >= 2:
            gain = recent[-1] - recent[-2]
            return gain < (1 - threshold) * 0.1  # Less than 10% of remaining coverage
        
        return False
    
    def _get_stop_words(self) -> Set[str]:
        """Get common stop words to filter from coverage analysis."""
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'our',
            'can', 'may', 'might', 'must', 'shall', 'from', 'up', 'down', 'out'
        }

class DynamicKController:
    """
    Controls dynamic k selection for retrieval based on:
    - Query complexity analysis
    - Marginal relevance scoring (ε-gain)
    - Coverage plateau detection
    - Context budget constraints
    """
    
    def __init__(self, params: Optional[RetrievalParams] = None):
        self.params = params or RetrievalParams()
        self.coverage_meter = CoverageMeter()
        logger.info(f"Initialized DynamicKController with k_min={self.params.k_min}, k_max={self.params.k_max}")
    
    async def determine_optimal_k(
        self,
        query: str,
        query_embedding: np.ndarray,
        qdrant_service,
        doc_filter: Optional[List[str]] = None
    ) -> RetrievalResult:
        """
        Determine optimal k through progressive retrieval with stopping conditions.
        """
        start_time = time.time()
        
        # Analyze query complexity
        complexity = QueryAnalyzer.analyze_complexity(query)
        logger.info(f"Query complexity: {complexity.value}")
        
        # Set initial k based on complexity
        if complexity == QueryComplexity.SIMPLE:
            initial_k = max(self.params.k_min, 3)
        elif complexity == QueryComplexity.COMPLEX:
            initial_k = min(self.params.k_max - 2, 8)
        else:  # MODERATE
            initial_k = (self.params.k_min + self.params.k_max) // 2
        
        # Progressive retrieval
        current_k = initial_k
        best_chunks: List[ChunkResult] = []
        total_tokens = 0
        stop_reason = "max_k_reached"
        
        logger.debug(f"Starting progressive retrieval with initial_k={initial_k}")
        
        while current_k <= self.params.k_max:
            # Retrieve current batch
            try:
                logger.info(f"Attempting Qdrant search with k={current_k}, threshold={self.params.score_threshold}")
                raw_results = await qdrant_service.search_similar(
                    query_embedding,
                    limit=current_k,
                    doc_filter=doc_filter,
                    score_threshold=self.params.score_threshold
                )
                
                logger.info(f"Qdrant search returned {len(raw_results) if raw_results else 0} results")
                
                if not raw_results:
                    stop_reason = "no_results"
                    logger.warning(f"No results found with threshold {self.params.score_threshold}")
                    break
                
                # Convert to ChunkResult objects
                chunks = []
                batch_tokens = 0
                
                for result in raw_results:
                    chunk = ChunkResult(
                        id=result['id'],
                        doc_id=result['doc_id'],
                        chunk_id=result['chunk_id'],
                        text=result['text'],
                        score=result['score'],
                        token_count=result.get('token_count', len(result['text'].split())),
                        chunk_index=result.get('chunk_index', 0),
                        metadata=result.get('metadata', {})
                    )
                    chunks.append(chunk)
                    batch_tokens += chunk.token_count
                
                # Check budget constraint
                if batch_tokens > self.params.budget_tokens:
                    # Trim to fit budget
                    chunks = self._trim_to_budget(chunks, self.params.budget_tokens)
                    batch_tokens = sum(chunk.token_count for chunk in chunks)
                    stop_reason = "budget_exceeded"
                    best_chunks = chunks
                    total_tokens = batch_tokens
                    break
                
                # Check marginal gain (ε-gain stopping condition)
                if len(best_chunks) > 0 and len(chunks) > len(best_chunks):
                    marginal_gain = self._calculate_marginal_gain(best_chunks, chunks)
                    if marginal_gain < self.params.epsilon_gain:
                        stop_reason = "marginal_gain_threshold"
                        break
                
                # Update best chunks
                best_chunks = chunks
                total_tokens = batch_tokens
                
                # Check coverage plateau
                coverage_score = self.coverage_meter.calculate_coverage(chunks, query_embedding)
                if self.coverage_meter.has_coverage_plateaued(self.params.coverage_threshold):
                    stop_reason = "coverage_plateau"
                    break
                
                # Prepare for next iteration
                current_k += 2  # Increment by 2 for efficiency
                
            except Exception as e:
                logger.error(f"Error in progressive retrieval at k={current_k}: {e}")
                stop_reason = "retrieval_error"
                break
        
        # Calculate final coverage
        final_coverage = self.coverage_meter.calculate_coverage(best_chunks, query_embedding) if best_chunks else 0.0
        
        retrieval_time = time.time() - start_time
        
        # Apply optional reranking
        rerank_time = None
        if self.params.rerank and best_chunks:
            rerank_start = time.time()
            best_chunks = await self._rerank_chunks(query, best_chunks)
            rerank_time = time.time() - rerank_start
        
        result = RetrievalResult(
            chunks=best_chunks,
            k_used=len(best_chunks),
            total_tokens=total_tokens,
            coverage_score=final_coverage,
            query_complexity=complexity,
            stop_reason=stop_reason,
            retrieval_time=retrieval_time,
            rerank_time=rerank_time,
            stats={
                'initial_k': initial_k,
                'max_k_attempted': current_k - 2,
                'budget_tokens': self.params.budget_tokens,
                'coverage_history': self.coverage_meter.coverage_history.copy()
            }
        )
        
        logger.info(
            f"Dynamic-k retrieval complete: k={result.k_used}, "
            f"tokens={result.total_tokens}, coverage={result.coverage_score:.3f}, "
            f"stop_reason={result.stop_reason}, time={result.retrieval_time:.3f}s"
        )
        
        return result
    
    def _calculate_marginal_gain(self, previous_chunks: List[ChunkResult], current_chunks: List[ChunkResult]) -> float:
        """Calculate marginal gain from adding more chunks."""
        if len(current_chunks) <= len(previous_chunks):
            return 0.0
        
        # Simple gain based on average score of new chunks
        new_chunks = current_chunks[len(previous_chunks):]
        if not new_chunks:
            return 0.0
        
        # Marginal gain is the average score of new chunks, adjusted for diminishing returns
        avg_new_score = sum(chunk.score for chunk in new_chunks) / len(new_chunks)
        
        # Apply diminishing returns factor
        position_penalty = 1.0 / (1.0 + 0.1 * len(previous_chunks))
        
        return avg_new_score * position_penalty
    
    def _trim_to_budget(self, chunks: List[ChunkResult], budget: int) -> List[ChunkResult]:
        """Trim chunks to fit within token budget, preserving highest scores."""
        # Sort by score descending
        sorted_chunks = sorted(chunks, key=lambda x: x.score, reverse=True)
        
        selected_chunks = []
        total_tokens = 0
        
        for chunk in sorted_chunks:
            if total_tokens + chunk.token_count <= budget:
                selected_chunks.append(chunk)
                total_tokens += chunk.token_count
            else:
                break
        
        return selected_chunks
    
    async def _rerank_chunks(self, query: str, chunks: List[ChunkResult]) -> List[ChunkResult]:
        """
        Apply optional local reranking to chunks.
        
        This is a placeholder for more sophisticated reranking algorithms.
        Currently implements a simple query-chunk similarity reranking.
        """
        if len(chunks) <= 1:
            return chunks
        
        try:
            # Simple reranking based on query-chunk text similarity
            query_words = set(query.lower().split())
            
            for chunk in chunks:
                chunk_words = set(chunk.text.lower().split())
                word_overlap = len(query_words & chunk_words) / max(len(query_words | chunk_words), 1)
                
                # Combine original score with word overlap
                chunk.rerank_score = 0.7 * chunk.score + 0.3 * word_overlap
            
            # Sort by rerank score
            chunks.sort(key=lambda x: x.rerank_score or x.score, reverse=True)
            
            logger.debug(f"Reranked {len(chunks)} chunks")
            
        except Exception as e:
            logger.warning(f"Error in reranking, using original order: {e}")
        
        return chunks

class RetrievalEngine:
    """Main retrieval engine that orchestrates the entire retrieval pipeline."""
    
    def __init__(self, profile: str = 'balanced'):
        self.profile = profile
        self.settings = get_settings()
        
        # Set parameters based on profile
        if profile == 'eco':
            self.params = RetrievalParams(
                k_min=3, k_max=6, budget_tokens=2000,
                epsilon_gain=0.08, rerank=False
            )
        elif profile == 'performance':
            self.params = RetrievalParams(
                k_min=4, k_max=12, budget_tokens=8000,
                epsilon_gain=0.03, rerank=True
            )
        else:  # balanced
            self.params = RetrievalParams(
                k_min=3, k_max=10, budget_tokens=4000,
                epsilon_gain=0.05, rerank=False
            )
        
        self.dynamic_k = DynamicKController(self.params)
        logger.info(f"Initialized RetrievalEngine with profile={profile}")
    
    async def retrieve_for_query(
        self,
        query: str,
        doc_filter: Optional[List[str]] = None,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> RetrievalResult:
        """
        Main retrieval method that handles the complete pipeline.
        
        Args:
            query: User query string
            doc_filter: Optional list of document IDs to filter by
            custom_params: Optional custom retrieval parameters
        
        Returns:
            RetrievalResult with chunks and analysis
        """
        logger.info(f"Starting retrieval for query: '{query[:50]}...'")
        
        # Apply custom parameters if provided
        if custom_params:
            current_params = RetrievalParams(**{
                **self.params.__dict__,
                **custom_params
            })
            dynamic_k = DynamicKController(current_params)
        else:
            dynamic_k = self.dynamic_k
        
        try:
            # Generate query embedding
            query_embedding = await embed_query(query, profile=self.profile)
            logger.info(f"Generated embedding with shape: {query_embedding.shape}")
            
            # Get services
            qdrant_service = await get_qdrant_service(self.profile)
            logger.info(f"Got Qdrant service")
            
            # Perform dynamic-k retrieval
            result = await dynamic_k.determine_optimal_k(
                query, query_embedding, qdrant_service, doc_filter
            )
            
            logger.info(f"Retrieval result: {len(result.chunks)} chunks, coverage: {result.coverage_score}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in retrieval pipeline: {e}")
            # Return empty result on error
            return RetrievalResult(
                chunks=[],
                k_used=0,
                total_tokens=0,
                coverage_score=0.0,
                query_complexity=QueryComplexity.SIMPLE,
                stop_reason="error",
                retrieval_time=0.0,
                stats={"error": str(e)}
            )

# Global retrieval engine instance
_retrieval_engine: Optional[RetrievalEngine] = None

async def get_retrieval_engine(profile: Optional[str] = None) -> RetrievalEngine:
    """Get or create the global retrieval engine instance."""
    global _retrieval_engine
    
    settings = get_settings()
    current_profile = profile or settings.performance_profile
    
    # Create new engine if needed or profile changed
    if _retrieval_engine is None or _retrieval_engine.profile != current_profile:
        _retrieval_engine = RetrievalEngine(current_profile)
    
    return _retrieval_engine

# Dependency injection function for FastAPI
async def get_retrieval_service(profile: Optional[str] = None) -> RetrievalEngine:
    """FastAPI dependency for retrieval service."""
    return await get_retrieval_engine(profile)


# Dynamic K controller function for testing
async def get_dynamic_k_controller():
    """Get a DynamicKController instance for testing."""
    from app.settings import get_settings
    settings = get_settings()
    params = RetrievalParams(
        k_min=settings.retrieval.k_min,
        k_max=settings.retrieval.k_max,
        token_budget=settings.retrieval.token_budget,
        rerank_enabled=settings.retrieval.rerank_enabled
    )
    return DynamicKController(params)
    """Get the dynamic K controller for testing purposes."""
    engine = await get_retrieval_engine()
    return engine.dynamic_k_controller
