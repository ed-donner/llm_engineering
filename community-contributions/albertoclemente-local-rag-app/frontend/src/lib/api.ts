import axios from 'axios'
import { API_BASE_URL } from './constants'
import type {
  Document,
  DocumentUploadRequest,
  DocumentUpdateRequest,
  QueryRequest,
  QueryResponse,
  SystemStatus,
  Settings
} from '@/types'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error: any) => {
    // Safely log error details
    const errorData = error.response?.data
    const errorMessage = error.message
    
    if (errorData && typeof errorData === 'object') {
      // eslint-disable-next-line no-console
      console.error('API Response Error:', JSON.stringify(errorData, null, 2))
    } else {
      const errorText = errorData !== undefined ? String(errorData) : String(errorMessage)
      // eslint-disable-next-line no-console
      console.error('API Response Error:', errorText)
    }
    
    return Promise.reject(error)
  }
)

// Document Management API
export const documentsApi = {
  // Get all documents
  getDocuments: async (): Promise<Document[]> => {
    const response = await api.get('/documents')
    return response.data.documents || []
  },

  // Upload document
  uploadDocument: async (data: DocumentUploadRequest): Promise<Document> => {
    const formData = new FormData()
    formData.append('file', data.file)
    if (data.title) formData.append('title', data.title)
    if (data.tags) formData.append('tags', JSON.stringify(data.tags))

    const response = await api.post('/documents', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    // Backend returns {document: Document, message: string, is_duplicate: boolean}
    return response.data.document
  },

  // Get document by ID
  getDocument: async (id: string): Promise<Document> => {
    const response = await api.get(`/documents/${id}`)
    return response.data
  },

  // Update document
  updateDocument: async (id: string, data: DocumentUpdateRequest): Promise<Document> => {
    const response = await api.put(`/documents/${id}`, data)
    return response.data
  },

  // Delete document
  deleteDocument: async (id: string): Promise<void> => {
    await api.delete(`/documents/${id}`)
  },

  // Reindex document
  reindexDocument: async (id: string): Promise<void> => {
    await api.post(`/documents/${id}/reindex`)
  },
}

// Query API
export const queryApi = {
  // Submit query
  query: async (data: QueryRequest): Promise<QueryResponse> => {
    const response = await api.post('/query', data)
    return response.data
  },
}

// System API
export const systemApi = {
  // Get system status
  getStatus: async (): Promise<SystemStatus> => {
    const response = await api.get('/status')
    return response.data
  },

  // Get settings
  getSettings: async (): Promise<Settings> => {
    const response = await api.get('/settings')
    return response.data
  },

  // Update settings
  updateSettings: async (data: Partial<Settings>): Promise<Settings> => {
    const response = await api.put('/settings', data)
    return response.data
  },

  // Health check
  healthCheck: async (): Promise<{ status: string }> => {
    const response = await api.get('/health')
    return response.data
  },
}

export default api
