"""
Adaptive chunking implementation with intelligent size selection.
Chooses chunk size 500–1350 tokens with 15–25% overlap based on document structure.
"""

import re
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from app.models import DocumentType
from app.settings import get_settings
from app.diagnostics import get_logger, performance_context

logger = get_logger(__name__)


class ChunkingStrategy(str, Enum):
    """Available chunking strategies"""
    FIXED = "fixed"
    ADAPTIVE = "adaptive"
    SEMANTIC = "semantic"


@dataclass
class ChunkingParams:
    """Parameters for chunking operation"""
    strategy: ChunkingStrategy = ChunkingStrategy.ADAPTIVE
    min_chunk_size: int = 500
    max_chunk_size: int = 1350
    min_overlap_percent: float = 15.0
    max_overlap_percent: float = 25.0
    preserve_structure: bool = True
    respect_sentence_boundaries: bool = True


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk"""
    chunk_id: str
    doc_id: str
    chunk_index: int
    start_char: int
    end_char: int
    token_count: int
    overlap_with_prev: int
    overlap_with_next: int
    structure_hints: Dict[str, Any]
    page_numbers: Optional[List[int]] = None


@dataclass
class ChunkedDocument:
    """Result of chunking operation"""
    doc_id: str
    chunks: List[str]
    metadata: List[ChunkMetadata]
    chunking_params: ChunkingParams
    rationale: str
    stats: Dict[str, Any]


class AdaptiveChunker:
    """Intelligent document chunking with adaptive sizing"""
    
    def __init__(self):
        self.settings = get_settings()
        # Rough token estimation: 1 token ≈ 0.75 words ≈ 4 characters
        self.chars_per_token = 4
        self.words_per_token = 0.75
    
    async def chunk_document(
        self, 
        doc_id: str,
        text: str, 
        document_structure: Dict[str, Any],
        doc_type: DocumentType,
        custom_params: Optional[ChunkingParams] = None
    ) -> ChunkedDocument:
        """
        Chunk a document using adaptive sizing based on content analysis.
        
        Args:
            doc_id: Document identifier
            text: Full document text
            document_structure: Structure analysis from parsing
            doc_type: Type of document
            custom_params: Optional custom chunking parameters
            
        Returns:
            ChunkedDocument with chunks and metadata
        """
        with performance_context("chunk_document", doc_id=doc_id, doc_type=doc_type.value):
            logger.info(f"Starting adaptive chunking for document {doc_id}")
            
            # Determine optimal chunking parameters
            params = custom_params or await self._determine_chunking_params(
                text, document_structure, doc_type
            )
            
            # Generate rationale for chunking decisions
            rationale = self._generate_rationale(document_structure, params, doc_type)
            
            # Perform the chunking
            chunks, metadata = await self._perform_chunking(
                doc_id, text, params, document_structure
            )
            
            # Calculate statistics
            stats = self._calculate_stats(chunks, metadata, text)
            
            logger.info(
                f"Chunked document {doc_id}: {len(chunks)} chunks, "
                f"avg size: {stats['avg_chunk_tokens']} tokens"
            )
            
            return ChunkedDocument(
                doc_id=doc_id,
                chunks=chunks,
                metadata=metadata,
                chunking_params=params,
                rationale=rationale,
                stats=stats
            )
    
    async def _determine_chunking_params(
        self, 
        text: str, 
        structure: Dict[str, Any], 
        doc_type: DocumentType
    ) -> ChunkingParams:
        """Determine optimal chunking parameters based on document analysis"""
        
        params = ChunkingParams()
        
        # Base adjustments by document type
        if doc_type == DocumentType.PDF:
            # PDFs often have complex layouts, use smaller chunks
            params.min_chunk_size = 500
            params.max_chunk_size = 1000
        elif doc_type == DocumentType.DOCX:
            # DOCX has good structure, can use larger chunks
            params.min_chunk_size = 600
            params.max_chunk_size = 1200
        elif doc_type == DocumentType.TXT:
            # Plain text, use medium chunks
            params.min_chunk_size = 550
            params.max_chunk_size = 1100
        elif doc_type == DocumentType.MD:
            # Markdown has explicit structure, use larger chunks
            params.min_chunk_size = 700
            params.max_chunk_size = 1350
        elif doc_type == DocumentType.EPUB:
            # Books often have chapters, use larger chunks
            params.min_chunk_size = 800
            params.max_chunk_size = 1350
        
        # Adjust based on document structure analysis
        density = structure.get('density', 'medium')
        has_structure = structure.get('has_structure', False)
        has_tables = structure.get('has_tables', False)
        
        if density == 'high':
            # Dense text (academic papers, technical docs)
            params.max_chunk_size = min(params.max_chunk_size, 1000)
            params.min_overlap_percent = 20.0  # More overlap for dense content
            params.max_overlap_percent = 25.0
        elif density == 'low':
            # Sparse text (bullet points, lists)
            params.min_chunk_size = max(params.min_chunk_size, 600)
            params.min_overlap_percent = 15.0  # Less overlap for sparse content
            params.max_overlap_percent = 20.0
        
        if has_structure:
            # Document has clear structure (headings, sections)
            params.preserve_structure = True
            params.max_chunk_size += 150  # Can use larger chunks with good structure
        
        if has_tables:
            # Tables should not be split
            params.preserve_structure = True
            params.respect_sentence_boundaries = False  # May need to break within sentences for tables
        
        # Adjust based on document length
        text_length = len(text)
        if text_length < 2000:  # Very short document
            params.min_chunk_size = min(params.min_chunk_size, 300)
            params.max_chunk_size = min(params.max_chunk_size, 800)
        elif text_length > 50000:  # Very long document
            params.min_chunk_size += 100
            params.max_chunk_size += 200
        
        # Apply performance profile adjustments
        if self.settings.profile.value == "eco":
            # Smaller chunks for better performance
            params.max_chunk_size = min(params.max_chunk_size, 1000)
        elif self.settings.profile.value == "performance":
            # Larger chunks for better accuracy
            params.min_chunk_size += 100
            params.max_chunk_size = min(params.max_chunk_size + 200, 1350)
        
        return params
    
    def _generate_rationale(
        self, 
        structure: Dict[str, Any], 
        params: ChunkingParams, 
        doc_type: DocumentType
    ) -> str:
        """Generate human-readable rationale for chunking decisions"""
        
        rationale_parts = []
        
        # Document type influence
        rationale_parts.append(f"Document type: {doc_type.value}")
        
        # Structure analysis influence
        density = structure.get('density', 'medium')
        rationale_parts.append(f"Content density: {density}")
        
        if structure.get('has_structure'):
            rationale_parts.append("Structured content detected (headings/sections)")
        
        if structure.get('has_tables'):
            rationale_parts.append("Tables detected - preserving table boundaries")
        
        if structure.get('has_lists'):
            rationale_parts.append("Lists detected - preserving list structure")
        
        # Parameter decisions
        rationale_parts.append(
            f"Chunk size: {params.min_chunk_size}-{params.max_chunk_size} tokens"
        )
        rationale_parts.append(
            f"Overlap: {params.min_overlap_percent:.1f}-{params.max_overlap_percent:.1f}%"
        )
        
        # Performance profile
        rationale_parts.append(f"Profile: {self.settings.profile.value}")
        
        return "; ".join(rationale_parts)
    
    async def _perform_chunking(
        self, 
        doc_id: str, 
        text: str, 
        params: ChunkingParams, 
        structure: Dict[str, Any]
    ) -> Tuple[List[str], List[ChunkMetadata]]:
        """Perform the actual chunking operation"""
        
        chunks = []
        metadata = []
        
        # Split text into sentences for better boundary detection
        sentences = self._split_into_sentences(text)
        
        # Find structural boundaries if preserving structure
        structural_boundaries = []
        if params.preserve_structure:
            structural_boundaries = self._find_structural_boundaries(text, structure)
        
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        sentence_start = 0
        for i, sentence in enumerate(sentences):
            # Check if adding this sentence would exceed max chunk size
            potential_chunk = current_chunk + (" " if current_chunk else "") + sentence
            potential_tokens = self._estimate_tokens(potential_chunk)
            
            # Decide whether to start a new chunk
            should_split = False
            
            if potential_tokens > params.max_chunk_size:
                should_split = True
            elif (potential_tokens > params.min_chunk_size and 
                  self._is_good_boundary(sentence_start + len(sentence), structural_boundaries)):
                should_split = True
            
            if should_split and current_chunk:
                # Create chunk
                chunk_tokens = self._estimate_tokens(current_chunk)
                current_end = sentence_start
                
                # Calculate overlap with previous chunk
                overlap_with_prev = 0
                if chunks:
                    overlap_tokens = int(chunk_tokens * params.min_overlap_percent / 100)
                    overlap_with_prev = overlap_tokens
                
                chunk_meta = ChunkMetadata(
                    chunk_id=f"{doc_id}#{chunk_index:06d}",
                    doc_id=doc_id,
                    chunk_index=chunk_index,
                    start_char=current_start,
                    end_char=current_end,
                    token_count=chunk_tokens,
                    overlap_with_prev=overlap_with_prev,
                    overlap_with_next=0,  # Will be set when next chunk is created
                    structure_hints=self._extract_structure_hints(current_chunk, structure)
                )
                
                chunks.append(current_chunk.strip())
                metadata.append(chunk_meta)
                
                # Update previous chunk's overlap_with_next
                if len(metadata) > 1:
                    metadata[-2].overlap_with_next = overlap_with_prev
                
                # Start new chunk with overlap
                if params.min_overlap_percent > 0:
                    overlap_sentences = self._get_overlap_sentences(
                        sentences, i, overlap_with_prev
                    )
                    current_chunk = " ".join(overlap_sentences)
                    current_start = current_end - len(current_chunk)
                else:
                    current_chunk = ""
                    current_start = sentence_start
                
                chunk_index += 1
            
            # Add current sentence to chunk
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
                if not should_split:
                    current_start = sentence_start
            
            sentence_start += len(sentence) + 1  # +1 for space
        
        # Add final chunk if there's remaining content
        if current_chunk.strip():
            chunk_tokens = self._estimate_tokens(current_chunk)
            
            # Calculate overlap with previous chunk
            overlap_with_prev = 0
            if chunks:
                overlap_tokens = int(chunk_tokens * params.min_overlap_percent / 100)
                overlap_with_prev = overlap_tokens
                metadata[-1].overlap_with_next = overlap_tokens
            
            chunk_meta = ChunkMetadata(
                chunk_id=f"{doc_id}#{chunk_index:06d}",
                doc_id=doc_id,
                chunk_index=chunk_index,
                start_char=current_start,
                end_char=len(text),
                token_count=chunk_tokens,
                overlap_with_prev=overlap_with_prev,
                overlap_with_next=0,
                structure_hints=self._extract_structure_hints(current_chunk, structure)
            )
            
            chunks.append(current_chunk.strip())
            metadata.append(chunk_meta)
        
        return chunks, metadata
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using simple heuristics"""
        # Simple sentence splitting - could be improved with nltk
        sentence_endings = re.compile(r'[.!?]+\s+')
        sentences = sentence_endings.split(text)
        
        # Clean up sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _find_structural_boundaries(self, text: str, structure: Dict[str, Any]) -> List[int]:
        """Find positions in text that represent good structural boundaries"""
        boundaries = []
        
        # Find headings (markdown-style or numbered)
        heading_pattern = r'^(#{1,6}\s+|[0-9]+\.?\s+[A-Z])'
        for match in re.finditer(heading_pattern, text, re.MULTILINE):
            boundaries.append(match.start())
        
        # Find paragraph breaks (double newlines)
        paragraph_pattern = r'\n\s*\n'
        for match in re.finditer(paragraph_pattern, text):
            boundaries.append(match.end())
        
        # Find list boundaries
        list_pattern = r'^[\s]*[-*•]\s+'
        for match in re.finditer(list_pattern, text, re.MULTILINE):
            boundaries.append(match.start())
        
        # Find table boundaries (simple heuristic)
        table_pattern = r'\|.*\|'
        table_positions = [match.start() for match in re.finditer(table_pattern, text)]
        if table_positions:
            # Add boundaries before and after table blocks
            boundaries.extend(table_positions)
        
        return sorted(set(boundaries))
    
    def _is_good_boundary(self, position: int, boundaries: List[int], tolerance: int = 100) -> bool:
        """Check if a position is near a structural boundary"""
        return any(abs(position - boundary) <= tolerance for boundary in boundaries)
    
    def _get_overlap_sentences(self, sentences: List[str], current_index: int, overlap_tokens: int) -> List[str]:
        """Get sentences for overlap from previous chunk"""
        overlap_sentences = []
        tokens_collected = 0
        
        # Work backwards from current position
        for i in range(current_index - 1, -1, -1):
            sentence_tokens = self._estimate_tokens(sentences[i])
            if tokens_collected + sentence_tokens <= overlap_tokens:
                overlap_sentences.insert(0, sentences[i])
                tokens_collected += sentence_tokens
            else:
                break
        
        return overlap_sentences
    
    def _extract_structure_hints(self, chunk: str, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structural hints from a chunk for later use"""
        hints = {}
        
        # Check for headings
        if re.search(r'^(#{1,6}\s+|[0-9]+\.?\s+[A-Z])', chunk, re.MULTILINE):
            hints['has_headings'] = True
        
        # Check for lists
        if re.search(r'^[\s]*[-*•]\s+', chunk, re.MULTILINE):
            hints['has_lists'] = True
        
        # Check for tables
        if '|' in chunk and chunk.count('|') > 2:
            hints['has_tables'] = True
        
        # Calculate text density
        word_count = len(chunk.split())
        line_count = len([line for line in chunk.split('\n') if line.strip()])
        if line_count > 0:
            hints['words_per_line'] = word_count / line_count
        
        return hints
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate number of tokens in text"""
        # Simple estimation: count words and adjust
        word_count = len(text.split())
        # Rough conversion: 1 token ≈ 0.75 words
        return int(word_count / self.words_per_token)
    
    def _calculate_stats(self, chunks: List[str], metadata: List[ChunkMetadata], original_text: str) -> Dict[str, Any]:
        """Calculate statistics about the chunking operation"""
        if not chunks:
            return {'error': 'No chunks generated'}
        
        chunk_sizes = [meta.token_count for meta in metadata]
        overlaps = [meta.overlap_with_prev for meta in metadata[1:]]  # Skip first chunk
        
        stats = {
            'total_chunks': len(chunks),
            'avg_chunk_tokens': sum(chunk_sizes) / len(chunk_sizes),
            'min_chunk_tokens': min(chunk_sizes),
            'max_chunk_tokens': max(chunk_sizes),
            'avg_overlap_tokens': sum(overlaps) / len(overlaps) if overlaps else 0,
            'total_original_tokens': self._estimate_tokens(original_text),
            'total_chunked_tokens': sum(chunk_sizes),
            'compression_ratio': sum(chunk_sizes) / self._estimate_tokens(original_text) if original_text else 1.0
        }
        
        return stats


# Global chunker instance
_chunker_instance: Optional[AdaptiveChunker] = None


def get_adaptive_chunker() -> AdaptiveChunker:
    """Get the global adaptive chunker instance"""
    global _chunker_instance
    if _chunker_instance is None:
        _chunker_instance = AdaptiveChunker()
    return _chunker_instance


# Utility functions for external use
async def chunk_parsed_document(
    doc_id: str,
    parsed_data: Dict[str, Any],
    custom_params: Optional[ChunkingParams] = None
) -> ChunkedDocument:
    """
    Convenience function to chunk a parsed document.
    
    Args:
        doc_id: Document identifier
        parsed_data: Parsed document data from parsing.py
        custom_params: Optional custom chunking parameters
        
    Returns:
        ChunkedDocument with chunks and metadata
    """
    chunker = get_adaptive_chunker()
    
    full_text = parsed_data.get('full_text', '')
    doc_type = DocumentType(parsed_data.get('document_type', 'txt'))
    structure = parsed_data.get('structure', {})
    
    return await chunker.chunk_document(
        doc_id=doc_id,
        text=full_text,
        document_structure=structure,
        doc_type=doc_type,
        custom_params=custom_params
    )


async def rechunk_document_with_params(
    doc_id: str,
    parsed_data: Dict[str, Any],
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
) -> ChunkedDocument:
    """
    Re-chunk a document with custom parameters.
    
    Args:
        doc_id: Document identifier
        parsed_data: Parsed document data
        chunk_size: Custom chunk size in tokens
        chunk_overlap: Custom overlap in tokens
        
    Returns:
        ChunkedDocument with new chunking
    """
    custom_params = ChunkingParams()
    
    if chunk_size:
        custom_params.min_chunk_size = max(300, chunk_size - 100)
        custom_params.max_chunk_size = min(1350, chunk_size + 100)
    
    if chunk_overlap:
        overlap_percent = (chunk_overlap / chunk_size * 100) if chunk_size else 20
        custom_params.min_overlap_percent = max(10, overlap_percent - 5)
        custom_params.max_overlap_percent = min(30, overlap_percent + 5)
    
    return await chunk_parsed_document(doc_id, parsed_data, custom_params)


# Global chunker instance
_chunker_instance: Optional[AdaptiveChunker] = None


async def get_chunking_service() -> AdaptiveChunker:
    """Get the global chunking service instance"""
    global _chunker_instance
    if _chunker_instance is None:
        _chunker_instance = AdaptiveChunker()
    return _chunker_instance
