export interface Document {
  id: string
  filename: string
  title?: string
  size: number
  upload_date: string  // Maps to backend addedAt
  file_type: string
  chunk_count?: number
  indexed: boolean
  tags: string[]
  metadata: Record<string, any>
  // Backend fields for compatibility
  name?: string
  sizeBytes?: number
  addedAt?: string
  lastIndexed?: string | null
  status?: string
  embedding_status?: string
  type?: string
  chunkCount?: number
  // AI-powered categorization fields
  categories?: string[]
  categoryConfidence?: number
  categoryGeneratedAt?: string
  categoryMethod?: 'auto' | 'manual' | 'llm' | 'keyword'
  categoryLanguage?: string
  categorySubcategories?: Record<string, string[]>
}

export interface DocumentUploadRequest {
  file: File
  title?: string
  tags?: string[]
}

export interface DocumentUpdateRequest {
  title?: string
  tags?: string[]
}

export interface CategoryInfo {
  name: string
  icon: string
  description: string
  subcategories: string[]
  document_count: number
  documentCount?: number  // Alias for compatibility
}

export interface CategoryStatistics {
  totalDocuments: number
  categorizedDocuments: number
  categoryCounts: Record<string, number>
  avgCategoriesPerDoc: number
  avgConfidence: number
  languageDistribution: Record<string, number>
  methodDistribution: Record<string, number>
}

export interface DocumentCategorizeRequest {
  force?: boolean
}

export interface DocumentUpdateCategoriesRequest {
  categories: string[]
}

export interface ChunkResult {
  content: string
  score: number
  metadata: {
    doc_id: string
    chunk_index: number
    page_number?: number
  }
}

export interface SourceInfo {
  document: string
  content: string
  score: number
}

export interface Citation {
  chunk_index: number
  doc_id: string
  doc_title: string
  page_number?: number
  relevance_score: number
  content_preview: string
}

export interface QueryRequest {
  query: string
  sessionId?: string
  k?: number
  doc_filter?: string[]
  min_score?: number
}

export interface QueryResponse {
  sessionId: string
  turnId: string
  message?: string
}

export interface StreamingQueryResponse {
  answer: string
  chunks: SourceInfo[]  // Updated to use SourceInfo from backend SOURCES event
  citations: Citation[]
  complexity: 'simple' | 'moderate' | 'complex'
  query_id: string
  processing_time: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  citations?: Citation[]
  query_id?: string
}

export interface SystemStatus {
  status: 'operational' | 'degraded' | 'offline' | 'error'
  cpu_usage?: number
  ram_usage?: number
  indexing_progress?: number
  offline: boolean
  model_name?: string
}

export interface Settings {
  rag_profile: 'eco' | 'balanced' | 'performance'
  chunk_size: number
  chunk_overlap: number
  retrieval_k: number
  min_relevance_score: number
  llm_temperature: number
  max_tokens: number
  system_prompt?: string
}

export type RAGProfile = typeof import('../lib/constants').RAG_PROFILES[keyof typeof import('../lib/constants').RAG_PROFILES]
export type QueryComplexity = typeof import('../lib/constants').QUERY_COMPLEXITY[keyof typeof import('../lib/constants').QUERY_COMPLEXITY]
