'use client'

import { useState, useRef } from 'react'
import { 
  FileText, 
  Upload, 
  Search, 
  Tag, 
  Filter,
  ChevronLeft,
  ChevronRight,
  Plus,
  MoreVertical
} from 'lucide-react'
import { useDocuments, useUploadDocument } from '@/hooks/api'
import { cn, formatFileSize, formatTimestamp } from '@/lib/utils'
import type { Document } from '@/types'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
}

export function Sidebar({ isOpen, onToggle }: SidebarProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTag, setSelectedTag] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { data: documentsData, isLoading, error } = useDocuments()
  const uploadDocument = useUploadDocument()

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      await uploadDocument.mutateAsync({
        file,
        title: file.name
      })
      // Reset the input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      console.error('Upload failed:', error)
    }
  }

  // Ensure documents is always an array and handle different response formats
  const documents: Document[] = Array.isArray(documentsData) 
    ? documentsData 
    : []

  // Filter documents based on search and tag
  const filteredDocuments = documents.filter((doc: Document) => {
    if (!doc) return false
    
    const matchesSearch = searchQuery === '' || 
      doc.filename?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.title?.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesTag = selectedTag === null || (doc.tags && doc.tags.includes(selectedTag))
    
    return matchesSearch && matchesTag
  })

  // Get all unique tags
  const allTags: string[] = Array.from(new Set(
    documents
      .filter((doc: Document) => doc && doc.tags)
      .flatMap((doc: Document) => doc.tags || [])
  ))

  if (!isOpen) {
    return (
      <div className="h-full flex flex-col items-center py-4">
        <button
          onClick={onToggle}
          className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg mb-4"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
        
        <div className="space-y-2">
          <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg">
            <FileText className="h-5 w-5" />
          </button>
          <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg">
            <Upload className="h-5 w-5" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Library</h2>
          <button
            onClick={onToggle}
            className="p-1 text-gray-500 hover:bg-gray-100 rounded"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        </div>

        {/* Search */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Upload Button */}
        <button 
          onClick={handleUploadClick}
          disabled={uploadDocument.isPending}
          className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Upload className="h-4 w-4" />
          <span className="text-sm font-medium">
            {uploadDocument.isPending ? 'Uploading...' : 'Upload Document'}
          </span>
        </button>
        
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.md,.doc,.docx,.pptx,.html,.htm,.png,.jpg,.jpeg,.tiff,.bmp,.asciidoc,.adoc"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {/* Tags Filter */}
      {allTags.length > 0 && (
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center space-x-2 mb-2">
            <Tag className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Tags</span>
          </div>
          <div className="flex flex-wrap gap-1">
            <button
              onClick={() => setSelectedTag(null)}
              className={cn(
                'px-2 py-1 text-xs rounded-full transition-colors',
                selectedTag === null
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              )}
            >
              All
            </button>
            {allTags.map((tag: string) => (
              <button
                key={tag}
                onClick={() => setSelectedTag(tag)}
                className={cn(
                  'px-2 py-1 text-xs rounded-full transition-colors',
                  selectedTag === tag
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                )}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Documents List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-gray-500">Loading...</div>
        ) : filteredDocuments.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            {documents.length === 0 ? 'No documents uploaded' : 'No documents match your filter'}
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {filteredDocuments.map((doc: Document) => (
              <DocumentItem key={doc.id} document={doc} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

interface DocumentItemProps {
  document: Document
}

function DocumentItem({ document }: DocumentItemProps) {
  return (
    <div className="p-3 rounded-lg hover:bg-gray-50 cursor-pointer group">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <FileText className="h-4 w-4 text-gray-400 flex-shrink-0" />
            <span className="text-sm font-medium text-gray-900 truncate">
              {document.title || document.filename || document.name}
            </span>
          </div>
          
          <div className="mt-1 text-xs text-gray-500">
            {formatFileSize(document.sizeBytes || document.size)} • {formatTimestamp(document.addedAt || document.upload_date)}
          </div>
          
          {document.tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {document.tags.slice(0, 3).map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                >
                  {tag}
                </span>
              ))}
              {document.tags.length > 3 && (
                <span className="text-xs text-gray-400">
                  +{document.tags.length - 3} more
                </span>
              )}
            </div>
          )}
          
          <div className="mt-1 flex items-center space-x-2">
            <div className={cn(
              'w-2 h-2 rounded-full',
              (document.indexed || document.status === 'indexed') ? 'bg-green-500' : 'bg-yellow-500'
            )} />
            <span className="text-xs text-gray-500">
              {(document.indexed || document.status === 'indexed') ? 'Indexed' : 'Processing...'}
            </span>
            {(document.chunk_count || document.chunkCount) && (
              <span className="text-xs text-gray-400">
                • {document.chunk_count || document.chunkCount} chunks
              </span>
            )}
          </div>
        </div>
        
        <button className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-gray-600 transition-opacity">
          <MoreVertical className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
