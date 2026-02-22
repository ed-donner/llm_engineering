"""
Document data models
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class DocumentChunk:
    """Represents a chunk of a document"""
    id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: Dict = field(default_factory=dict)
    
    def __str__(self):
        preview = self.content[:100] + "..." if len(self.content) > 100 else self.content
        return f"Chunk {self.chunk_index}: {preview}"

@dataclass
class Document:
    """Represents a complete document"""
    id: str
    filename: str
    filepath: str
    content: str
    chunks: List[DocumentChunk]
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def num_chunks(self) -> int:
        return len(self.chunks)
    
    @property
    def total_chars(self) -> int:
        return len(self.content)
    
    @property
    def extension(self) -> str:
        return self.metadata.get('extension', '')
    
    def __str__(self):
        return f"Document: {self.filename} ({self.num_chunks} chunks, {self.total_chars} chars)"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'filename': self.filename,
            'filepath': self.filepath,
            'content': self.content[:500] + '...' if len(self.content) > 500 else self.content,
            'num_chunks': self.num_chunks,
            'total_chars': self.total_chars,
            'extension': self.extension,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }

@dataclass
class SearchResult:
    """Represents a search result from the vector database"""
    chunk: DocumentChunk
    score: float
    document_id: str
    document_name: str
    
    def __str__(self):
        return f"{self.document_name} (score: {self.score:.2f})"

@dataclass
class Summary:
    """Represents a document summary"""
    document_id: str
    document_name: str
    summary_text: str
    key_points: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __str__(self):
        return f"Summary of {self.document_name}: {self.summary_text[:100]}..."
