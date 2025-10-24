import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi, queryApi, systemApi } from '@/lib/api'
import { WS_BASE_URL, API_BASE_URL } from '@/lib/constants'
import type {
  Document,
  DocumentUploadRequest,
  DocumentUpdateRequest,
  QueryRequest,
  QueryResponse,
  StreamingQueryResponse,
  Citation,
  Settings,
  CategoryInfo,
  CategoryStatistics,
  DocumentCategorizeRequest
} from '@/types'
import toast from 'react-hot-toast'

// Query Keys
export const queryKeys = {
  documents: ['documents'] as const,
  document: (id: string) => ['documents', id] as const,
  systemStatus: ['system', 'status'] as const,
  settings: ['system', 'settings'] as const,
  health: ['system', 'health'] as const,
  categories: ['categories'] as const,
  categoryStats: ['categories', 'statistics'] as const,
}

// Helper function to extract error message
function extractErrorMessage(error: any): string {
  // Handle FastAPI validation errors
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail
    
    // If detail is an array (validation errors)
    if (Array.isArray(detail)) {
      return detail.map(err => `${err.loc?.join('.')}: ${err.msg}`).join(', ')
    }
    
    // If detail is a string
    if (typeof detail === 'string') {
      return detail
    }
    
    // If detail is an object, try to extract meaningful message
    if (typeof detail === 'object' && detail.msg) {
      return detail.msg
    }
  }
  
  // Fallback to generic message
  return error.message || 'An unexpected error occurred'
}

// Document Hooks
export function useDocuments() {
  return useQuery({
    queryKey: queryKeys.documents,
    queryFn: documentsApi.getDocuments,
    staleTime: 0, // Force immediate refresh to pick up status changes
  })
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: queryKeys.document(id),
    queryFn: () => documentsApi.getDocument(id),
    enabled: !!id,
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: documentsApi.uploadDocument,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents })
      const docName = data.name || data.filename || 'Document'
      toast.success(`Document "${docName}" uploaded successfully`)
    },
    onError: (error: any) => {
      const message = extractErrorMessage(error) || 'Failed to upload document'
      toast.error(message)
    },
  })
}

export function useUpdateDocument() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: DocumentUpdateRequest }) =>
      documentsApi.updateDocument(id, data),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents })
      queryClient.invalidateQueries({ queryKey: queryKeys.document(variables.id) })
      toast.success(`Document "${data.filename}" updated successfully`)
    },
    onError: (error: any) => {
      const message = extractErrorMessage(error) || 'Failed to update document'
      toast.error(message)
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: documentsApi.deleteDocument,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents })
      queryClient.removeQueries({ queryKey: queryKeys.document(id) })
      toast.success('Document deleted successfully')
    },
    onError: (error: any) => {
      const message = extractErrorMessage(error) || 'Failed to delete document'
      toast.error(message)
    },
  })
}

export function useReindexDocument() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: documentsApi.reindexDocument,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents })
      queryClient.invalidateQueries({ queryKey: queryKeys.document(id) })
      toast.success('Document reindexed successfully')
    },
    onError: (error: any) => {
      const message = extractErrorMessage(error) || 'Failed to reindex document'
      toast.error(message)
    },
  })
}

// Query Hook with WebSocket streaming and fallback
export function useSubmitQuery() {
  return useMutation({
    mutationFn: async (data: QueryRequest & { 
      onStreamToken?: (token: string) => void,
      onStreamingStart?: () => void,
      onStreamingEnd?: () => void 
    }) => {
      // Configurable stream timeout; disabled by default (<= 0)
      const STREAM_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_STREAM_TIMEOUT_MS ?? 0)
      try {
        // Step 1: Start the query via REST API
        const response = await queryApi.query({
          query: data.query,
          sessionId: data.sessionId
        })
        const { sessionId, turnId } = response
        
        // Step 2: Connect to WebSocket for streaming response
        return new Promise<StreamingQueryResponse>((resolve, reject) => {
          const wsUrl = `${WS_BASE_URL}/ws/stream?session_id=${sessionId}&turn_id=${turnId}`
          console.log('🔗 Connecting to WebSocket:', wsUrl)
          const ws = new WebSocket(wsUrl)
          
          let answer = ''
          const citations: Citation[] = []
          let sources: any[] = []
          const sourcesByLabel = new Map<number, any>()
          let isComplete = false
          
          ws.onopen = () => {
            console.log('✅ WebSocket connected for query streaming')
            data.onStreamingStart?.()
          }
          
          ws.onmessage = (event) => {
            try {
              console.log('📨 WebSocket message received:', event.data)
              const message = JSON.parse(event.data)
              
              switch (message.event) {
                case 'START':
                  console.log('Query processing started:', message.meta)
                  break
                  
                case 'TOKEN':
                  if (message.text) {
                    answer += message.text
                    data.onStreamToken?.(message.text)
                  }
                  break
                  
                case 'CITATION': {
                  const label: number = message.label
                  const src = sourcesByLabel.get(label)
                  const inferredDocId = message.chunkId?.split('#')[0] || src?.docId || ''
                  const inferredTitle = src?.document || src?.filename || src?.name || src?.docId || inferredDocId
                  citations.push({
                    chunk_index: label,
                    doc_id: inferredDocId,
                    doc_title: inferredTitle,
                    page_number: src?.pageStart,
                    relevance_score: typeof src?.score === 'number' ? src.score : 0.8,
                    content_preview: src?.text || src?.content || ''
                  })
                  break
                }
                  
                case 'SOURCES': {
                  console.log('🔎 SOURCES event payload:', message.sources)
                  const rawSources = message.sources || []
                  // Normalize and index by label for later citation enrichment
                  sources = rawSources.map((s: any) => {
                    const label = s.label ?? s.index ?? 0
                    const docId = s.docId ?? s.doc_id ?? s.documentId ?? s.document_id ?? ''
                    const text = s.text ?? s.content ?? s.snippet ?? ''
                    const score = typeof s.score === 'number' ? s.score : (typeof s.similarity === 'number' ? s.similarity : 0)
                    const pageStart = s.pageStart ?? s.page_number ?? s.page ?? undefined
                    const document = s.document ?? s.filename ?? s.name ?? docId
                    const chunkId = s.chunkId ?? s.chunk_id ?? undefined
                    const normalized = { label, docId, chunkId, pageStart, text, score, document }
                    sourcesByLabel.set(label, normalized)
                    return normalized
                  })
                  break
                }
                  
                case 'END':
                  isComplete = true
                  data.onStreamingEnd?.()
                  ws.close()
                  // Build SourceInfo[] for UI and index by docId
                  const sourcesByDocId = new Map<string, any>()
                  const chunkSources = (sources || []).map((s: any) => {
                    if (s?.docId) sourcesByDocId.set(String(s.docId), s)
                    return {
                    document: s.document ?? s.docId ?? 'Unknown',
                    content: s.text ?? s.content ?? '',
                    score: typeof s.score === 'number' ? s.score : 0
                    }
                  })

                  // Enrich citations with mapped source details
                  const enrichedCitations: Citation[] = citations.map((c) => {
                    let s = sourcesByLabel.get(c.chunk_index)
                    if (!s && c.doc_id) {
                      s = sourcesByDocId.get(String(c.doc_id))
                    }
                    return {
                      chunk_index: c.chunk_index,
                      doc_id: (s?.docId || c.doc_id || ''),
                      doc_title: (s?.document || c.doc_title || s?.docId || c.doc_id || ''),
                      page_number: (s?.pageStart ?? c.page_number),
                      relevance_score: (typeof s?.score === 'number' ? s.score : c.relevance_score),
                      content_preview: (s?.text || c.content_preview || '')
                    }
                  })

                  resolve({
                    answer,
                    chunks: chunkSources, // normalized sources list
                    citations: enrichedCitations,
                    complexity: 'moderate' as const,
                    query_id: turnId,
                    processing_time: message.stats?.ms || 0
                  })
                  break
                  
                case 'ERROR':
                  isComplete = true
                  data.onStreamingEnd?.()
                  ws.close()
                  reject(new Error(message.detail || 'Streaming error'))
                  break
              }
            } catch (e) {
              console.error('Error parsing WebSocket message:', e)
            }
          }
          
          ws.onerror = (error) => {
            console.error('❌ WebSocket error:', error)
            if (!isComplete) {
              data.onStreamingEnd?.()
              // Fallback: provide a simple response instead of failing
              console.log('🔄 WebSocket failed, using fallback response')
              resolve({
                answer: `I found information related to "${data.query}" in your documents. However, the streaming connection failed. Please check the browser console for details and try again.`,
                chunks: [],
                citations: [],
                complexity: 'moderate' as const,
                query_id: turnId,
                processing_time: 0
              })
            }
          }
          
          ws.onclose = (event) => {
            console.log('🔌 WebSocket connection closed:', event.code, event.reason)
            if (!isComplete) {
              data.onStreamingEnd?.()
              console.log('🔄 WebSocket closed unexpectedly, using fallback response')
              resolve({
                answer: `Query processed but connection closed. Session: ${sessionId}, Turn: ${turnId}. Please check the backend logs for details.`,
                chunks: [],
                citations: [],
                complexity: 'moderate' as const,
                query_id: turnId,
                processing_time: 0
              })
            }
          }
          
          // Optional timeout: only set if STREAM_TIMEOUT_MS > 0
          if (STREAM_TIMEOUT_MS > 0) {
            setTimeout(() => {
              if (!isComplete) {
                data.onStreamingEnd?.()
                ws.close()
                resolve({
                  answer: `The query is still processing after ${Math.round(STREAM_TIMEOUT_MS/1000)} seconds. The connection was closed due to client timeout.`,
                  chunks: [],
                  citations: [],
                  complexity: 'moderate' as const,
                  query_id: turnId,
                  processing_time: STREAM_TIMEOUT_MS
                })
              }
            }, STREAM_TIMEOUT_MS)
          }
        })
      } catch (error) {
        console.error('Query API error:', error)
        throw error
      }
    },
    onError: (error: any) => {
      const message = extractErrorMessage(error) || 'Failed to process query'
      toast.error(message)
    },
  })
}

// System Hooks
export function useSystemStatus() {
  return useQuery({
    queryKey: queryKeys.systemStatus,
    queryFn: systemApi.getStatus,
    refetchInterval: 10000, // Refetch every 10 seconds
    staleTime: 5000, // Consider stale after 5 seconds
  })
}

export function useSettings() {
  return useQuery({
    queryKey: queryKeys.settings,
    queryFn: systemApi.getSettings,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useUpdateSettings() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: systemApi.updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settings })
      toast.success('Settings updated successfully')
    },
    onError: (error: any) => {
      const message = extractErrorMessage(error) || 'Failed to update settings'
      toast.error(message)
    },
  })
}

export function useHealthCheck() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: systemApi.healthCheck,
    refetchInterval: 30000, // Check every 30 seconds
    retry: 3,
    staleTime: 10000,
  })
}

// Conversation History Hooks
export const conversationKeys = {
  all: ['conversations'] as const,
  detail: (sessionId: string) => ['conversations', sessionId] as const,
  stats: ['conversations', 'stats'] as const,
}

export function useConversations() {
  return useQuery({
    queryKey: conversationKeys.all,
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/conversations`)
      if (!response.ok) throw new Error('Failed to fetch conversations')
      return response.json()
    },
    staleTime: 30000, // 30 seconds
  })
}

export function useConversationDetail(sessionId: string) {
  return useQuery({
    queryKey: conversationKeys.detail(sessionId),
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/conversations/${sessionId}`)
      if (!response.ok) throw new Error('Failed to fetch conversation')
      return response.json()
    },
    enabled: !!sessionId,
    refetchOnWindowFocus: false, // Don't refetch when switching tabs/windows to preserve optimistic UI
  })
}

export function useDeleteConversation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await fetch(`${API_BASE_URL}/api/conversations/${sessionId}`, {
        method: 'DELETE',
      })
      if (!response.ok) throw new Error('Failed to delete conversation')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: conversationKeys.all })
      toast.success('Conversation deleted successfully')
    },
    onError: (error: any) => {
      const message = extractErrorMessage(error) || 'Failed to delete conversation'
      toast.error(message)
    },
  })
}

export function useConversationStats() {
  return useQuery({
    queryKey: conversationKeys.stats,
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/conversations/stats`)
      if (!response.ok) throw new Error('Failed to fetch stats')
      return response.json()
    },
    staleTime: 60000, // 1 minute
  })
}

export function useGenerateConversationTitle() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await fetch(`${API_BASE_URL}/api/conversations/${sessionId}/generate-title`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to generate title')
      return response.json()
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: conversationKeys.all })
      queryClient.invalidateQueries({ queryKey: conversationKeys.detail(data.session_id) })
      toast.success('Title generated successfully')
    },
    onError: (error: any) => {
      const message = extractErrorMessage(error) || 'Failed to generate title'
      toast.error(message)
    },
  })
}

// Category Management Hooks
export function useCategories() {
  return useQuery({
    queryKey: queryKeys.categories,
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/categories`)
      if (!response.ok) throw new Error('Failed to fetch categories')
      return response.json() as Promise<{ categories: CategoryInfo[], totalCategories: number }>
    },
    staleTime: 5 * 60 * 1000, // 5 minutes - categories don't change often
  })
}

export function useCategoryStatistics() {
  return useQuery({
    queryKey: queryKeys.categoryStats,
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/categories/statistics`)
      if (!response.ok) throw new Error('Failed to fetch category statistics')
      return response.json() as Promise<CategoryStatistics>
    },
    staleTime: 60000, // 1 minute
  })
}

export function useCategorizeDocument() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ 
      docId, 
      force = false 
    }: { 
      docId: string
      force?: boolean 
    }) => {
      const response = await fetch(`${API_BASE_URL}/api/documents/${docId}/categorize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ force }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to categorize document')
      }
      return response.json()
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents })
      queryClient.invalidateQueries({ queryKey: queryKeys.document(variables.docId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.categoryStats })
      toast.success('Document categorized successfully')
    },
    onError: (error: any) => {
      const message = extractErrorMessage(error) || 'Failed to categorize document'
      toast.error(message)
    },
  })
}

export function useUpdateDocumentCategories() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ 
      docId, 
      categories 
    }: { 
      docId: string
      categories: string[] 
    }) => {
      const response = await fetch(`${API_BASE_URL}/api/documents/${docId}/categories`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ categories }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to update categories')
      }
      return response.json()
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents })
      queryClient.invalidateQueries({ queryKey: queryKeys.document(variables.docId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.categoryStats })
      toast.success('Categories updated successfully')
    },
    onError: (error: any) => {
      const message = extractErrorMessage(error) || 'Failed to update categories'
      toast.error(message)
    },
  })
}



