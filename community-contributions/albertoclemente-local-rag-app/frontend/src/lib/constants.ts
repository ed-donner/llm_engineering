// API Base URL
// Support both NEXT_PUBLIC_API_BASE_URL and NEXT_PUBLIC_API_URL for flexibility
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000'

// WebSocket URL for streaming
// Support both NEXT_PUBLIC_WS_BASE_URL and NEXT_PUBLIC_WS_URL
export const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_BASE_URL ||
  process.env.NEXT_PUBLIC_WS_URL ||
  'ws://localhost:8000'

// Supported file types for upload
export const SUPPORTED_FILE_TYPES = [
  'application/pdf',
  'text/plain',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/msword'
]

// File extensions mapping
export const FILE_EXTENSIONS = {
  'application/pdf': '.pdf',
  'text/plain': '.txt',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
  'application/msword': '.doc'
}

// RAG Configuration
export const RAG_PROFILES = {
  ECO: 'eco',
  BALANCED: 'balanced', 
  PERFORMANCE: 'performance'
} as const

// Query complexity levels
export const QUERY_COMPLEXITY = {
  SIMPLE: 'simple',
  MODERATE: 'moderate',
  COMPLEX: 'complex'
} as const
