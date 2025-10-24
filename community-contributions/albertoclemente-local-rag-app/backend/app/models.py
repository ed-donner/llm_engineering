"""
Pydantic models for API requests/responses and internal data structures.
Follows the specifications from LLD and UI Spec.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict


class DocumentType(str, Enum):
    """Supported document types"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    EPUB = "epub"
    HTML = "html"
    PPTX = "pptx"


class DocumentStatus(str, Enum):
    """Document indexing status"""
    INDEXED = "indexed"
    NEEDS_REINDEX = "needs-reindex"
    ERROR = "error"
    INDEXING = "indexing"


class EmbeddingStatus(str, Enum):
    """Document embedding status"""
    NOT_INDEXED = "not_indexed"
    INDEXED = "indexed"
    INDEXING = "indexing"
    ERROR = "error"


class Profile(str, Enum):
    """System performance profiles"""
    ECO = "eco"
    BALANCED = "balanced"
    PERFORMANCE = "performance"


class UiStatus(str, Enum):
    """UI streaming status"""
    IDLE = "idle"
    RETRIEVING = "retrieving"
    STREAMING = "streaming"
    COMPLETE = "complete"
    ERROR = "error"


class Document(BaseModel):
    """Document metadata model"""
    id: str
    name: str
    type: DocumentType
    size_bytes: int = Field(alias="sizeBytes")
    pages: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    status: DocumentStatus = DocumentStatus.INDEXING
    embedding_status: EmbeddingStatus = EmbeddingStatus.NOT_INDEXED
    added_at: datetime = Field(alias="addedAt", default_factory=datetime.utcnow)
    last_indexed: Optional[float] = Field(alias="lastIndexed", default=None)
    chunk_params: Optional[Dict[str, Any]] = None
    chunk_count: int = Field(alias="chunkCount", default=0)
    
    # AI-powered categorization fields
    categories: List[str] = Field(default_factory=list)
    category_confidence: Optional[float] = Field(alias="categoryConfidence", default=None)
    category_generated_at: Optional[datetime] = Field(alias="categoryGeneratedAt", default=None)
    category_method: str = Field(alias="categoryMethod", default="auto")  # "auto", "manual", "llm", "keyword"
    category_language: Optional[str] = Field(alias="categoryLanguage", default=None)
    category_subcategories: Dict[str, List[str]] = Field(alias="categorySubcategories", default_factory=dict)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class DocumentUploadResponse(BaseModel):
    """Response for document upload"""
    document: Document
    message: str = "Document uploaded successfully"
    is_duplicate: bool = False


class DocumentListResponse(BaseModel):
    """Response for document listing"""
    documents: List[Document]
    total: int


class DocumentUpdateRequest(BaseModel):
    """Request for updating document metadata"""
    name: Optional[str] = None
    tags: Optional[List[str]] = None


class DocumentReindexRequest(BaseModel):
    """Request for manual reindexing with custom params"""
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    force: bool = False


class DocumentCategorizeRequest(BaseModel):
    """Request for manual document categorization"""
    force: bool = False  # Force re-categorization even if already categorized


class DocumentUpdateCategoriesRequest(BaseModel):
    """Request for updating document categories manually"""
    categories: List[str] = Field(min_length=1, max_length=5)


class CategoryInfo(BaseModel):
    """Category information with metadata"""
    name: str
    icon: str
    description: str
    subcategories: List[str] = Field(default_factory=list)
    document_count: int = 0


class CategoryListResponse(BaseModel):
    """Response for category listing"""
    categories: List[CategoryInfo]
    total_categories: int = Field(alias="totalCategories")
    
    model_config = ConfigDict(populate_by_name=True)


class CategoryStatistics(BaseModel):
    """Statistics about document categories"""
    total_documents: int = Field(alias="totalDocuments")
    categorized_documents: int = Field(alias="categorizedDocuments")
    category_counts: Dict[str, int] = Field(alias="categoryCounts")
    avg_categories_per_doc: float = Field(alias="avgCategoriesPerDoc")
    avg_confidence: float = Field(alias="avgConfidence")
    language_distribution: Dict[str, int] = Field(alias="languageDistribution")
    method_distribution: Dict[str, int] = Field(alias="methodDistribution")
    
    model_config = ConfigDict(populate_by_name=True)


class Citation(BaseModel):
    """Citation reference"""
    label: int
    doc_id: str = Field(alias="docId")
    chunk_id: str = Field(alias="chunkId")
    page_start: Optional[int] = Field(alias="pageStart", default=None)

    model_config = ConfigDict(populate_by_name=True)
class SourceItem(BaseModel):
    """Retrieved source item with snippet"""
    label: int
    doc_id: str = Field(alias="docId")
    chunk_id: str = Field(alias="chunkId")
    page_start: Optional[int] = Field(alias="pageStart", default=None)
    text: str
    score: Optional[float] = None

    model_config = ConfigDict(populate_by_name=True)
class ChatTurn(BaseModel):
    """Chat turn (query/response pair)"""
    id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    citations: Optional[List[Citation]] = None
    created_at: datetime = Field(alias="createdAt", default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class QueryRequest(BaseModel):
    """Request for starting a query"""
    query: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(alias="sessionId")
    
    model_config = ConfigDict(populate_by_name=True)
class QueryResponse(BaseModel):
    """Response from query initiation"""
    session_id: str = Field(alias="sessionId")
    turn_id: str = Field(alias="turnId")
    message: str = "Query started"

    model_config = ConfigDict(populate_by_name=True)

# Conversation context models
class ConversationTurn(BaseModel):
    """A single turn in a conversation"""
    turn_id: str
    query: str
    response: str
    timestamp: datetime
    sources: List[Dict] = Field(default_factory=list)

class ConversationSession(BaseModel):
    """A conversation session with history"""
    session_id: str
    turns: List[ConversationTurn] = Field(default_factory=list)
    created_at: datetime
    last_active: datetime
    
    def add_turn(self, turn_id: str, query: str, response: str, sources: List[Dict] = None):
        """Add a new turn to the conversation"""
        turn = ConversationTurn(
            turn_id=turn_id,
            query=query,
            response=response,
            timestamp=datetime.now(),
            sources=sources or []
        )
        self.turns.append(turn)
        self.last_active = datetime.now()
    
    def get_context_for_llm(self, max_turns: int = 5) -> str:
        """Get formatted conversation context for LLM"""
        if not self.turns:
            return ""
        
        # Get recent turns (up to max_turns)
        recent_turns = self.turns[-max_turns:]
        
        context_parts = ["Previous conversation:"]
        for turn in recent_turns:
            context_parts.append(f"User: {turn.query}")
            context_parts.append(f"Assistant: {turn.response}")
        
        return "\n".join(context_parts)

# WebSocket event models
class StreamEventBase(BaseModel):
    """Base class for streaming events"""
    event: str


class StartEvent(StreamEventBase):
    """Stream start event"""
    event: str = "START"
    meta: Dict[str, str]  # {"model": "model_name"}


class TokenEvent(StreamEventBase):
    """Token streaming event"""
    event: str = "TOKEN"
    text: str


class CitationEvent(StreamEventBase):
    """Citation event"""
    event: str = "CITATION"
    label: int
    chunk_id: str = Field(alias="chunkId")

    model_config = ConfigDict(populate_by_name=True)


class SourcesEvent(StreamEventBase):
    """Sources event containing detailed source information"""
    event: str = "SOURCES"
    sources: List[Dict[str, Any]]
class EndEvent(StreamEventBase):
    """Stream end event"""
    event: str = "END"
    stats: Dict[str, Union[int, float, str]]  # {"tokens": N, "ms": T, "complexity": "simple"}


class ErrorEvent(StreamEventBase):
    """Stream error event"""
    event: str = "ERROR"
    error_code: str
    detail: str


# Union type for all streaming events
StreamEvent = Union[StartEvent, TokenEvent, CitationEvent, SourcesEvent, EndEvent, ErrorEvent]


class Settings(BaseModel):
    """System settings"""
    profile: Profile = Profile.BALANCED
    chunking_mode: str = "auto"  # "auto" | "manual"
    k_min: int = Field(default=3, ge=1, le=20)
    k_max: int = Field(default=10, ge=1, le=50)
    context_budget: int = Field(default=4000, ge=1000, le=32000)
    encryption_enabled: bool = False
    model_preset: str = "default"


class SystemStatus(BaseModel):
    """System status information"""
    status: str = "ready"
    cpu_usage: Optional[float] = None  # Percentage 0-100
    ram_usage: Optional[int] = None    # Bytes (used for display in GB)
    indexing_progress: Optional[int] = None  # 0-100; hide when None or 100
    offline: bool = False  # Changed default to False for local operation
    model_name: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None
