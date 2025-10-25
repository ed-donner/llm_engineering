'use client'

import React, { useState } from 'react'
import { useDocuments } from '@/hooks/api'
import { BookOpen, Eye, ExternalLink, ChevronDown, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Citation, ChunkResult, SourceInfo } from '@/types'

interface SourcesPanelProps {
  sources?: SourceInfo[]
  citations?: Citation[]
}

export function SourcesPanel({ sources = [], citations = [] }: SourcesPanelProps) {
  const [activeTab, setActiveTab] = useState<'citations' | 'chunks'>('citations')
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set())

  // Debug logging
  React.useEffect(() => {
    console.log('🗂️ SourcesPanel: Props updated:', {
      sourcesCount: sources.length,
      citationsCount: citations.length,
      sources: sources,
      citations: citations
    })
  }, [sources, citations])

  // Use provided data or fall back to empty arrays
  const displayCitations = citations.length > 0 ? citations : []
  const displaySources = sources.length > 0 ? sources : []

  const toggleExpanded = (id: string) => {
    const newExpanded = new Set(expandedItems)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedItems(newExpanded)
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Sources & Context</h3>
        
        {/* Debug Info - TEMPORARY */}
        <div className="mb-3 p-2 bg-yellow-100 border border-yellow-300 rounded text-xs">
          <strong>DEBUG:</strong> Sources: {sources.length}, Citations: {citations.length}
          <br />
          Last update: {new Date().toLocaleTimeString()}
        </div>
        
        {/* Tabs */}
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('citations')}
            className={cn(
              'flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors',
              activeTab === 'citations'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            )}
          >
            Citations
          </button>
          <button
            onClick={() => setActiveTab('chunks')}
            className={cn(
              'flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors',
              activeTab === 'chunks'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            )}
          >
            Chunks
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'citations' ? (
          <CitationsView 
            citations={displayCitations}
            expandedItems={expandedItems}
            onToggleExpanded={toggleExpanded}
          />
        ) : (
          <ChunksView 
            chunks={displaySources}
            expandedItems={expandedItems}
            onToggleExpanded={toggleExpanded}
          />
        )}
      </div>

      {/* Coverage Meter */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Coverage</span>
          <span className="text-sm text-gray-500">85%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full" 
            style={{ width: '85%' }}
          />
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Query covered by available sources
        </p>
      </div>
    </div>
  )
}

interface CitationsViewProps {
  citations: Citation[]
  expandedItems: Set<string>
  onToggleExpanded: (id: string) => void
}

function CitationsView({ citations, expandedItems, onToggleExpanded }: CitationsViewProps) {
  // Get document metadata for title mapping
  const { data: docsData } = useDocuments()
  const docMap = React.useMemo(() => {
    const map = new Map<string, string>()
    if (Array.isArray(docsData)) {
      for (const doc of docsData) {
        map.set(doc.id, doc.title || doc.filename || doc.name || doc.id)
      }
    }
    return map
  }, [docsData])
  return (
    <div className="p-4 space-y-3">
      {citations.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          <BookOpen className="h-8 w-8 mx-auto mb-2 text-gray-400" />
          <p>No citations yet</p>
          <p className="text-sm">Ask a question to see relevant sources</p>
        </div>
      ) : (
        citations.map((citation, index) => {
          const itemId = `citation-${index}`
          const isExpanded = expandedItems.has(itemId)
          
          return (
            <div key={index} className="border border-gray-200 rounded-lg overflow-hidden">
              <div className="p-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="inline-flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                        {index + 1}
                      </span>
                      <span className="text-sm font-medium text-gray-900">
                        {docMap.get(citation.doc_id) || citation.doc_title || citation.doc_id}
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-3 text-xs text-gray-500 mb-2">
                      {citation.page_number && (
                        <span>Page {citation.page_number}</span>
                      )}
                      <span>Relevance: {(citation.relevance_score * 100).toFixed(0)}%</span>
                    </div>
                    
                    <p className="text-sm text-gray-700 line-clamp-3">
                      {isExpanded ? citation.content_preview : `${citation.content_preview.slice(0, 150)}...`}
                    </p>
                  </div>
                  
                  <div className="flex items-center space-x-1 ml-2">
                    <button
                      onClick={() => onToggleExpanded(itemId)}
                      className="p-1 text-gray-400 hover:text-gray-600"
                    >
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </button>
                    <button className="p-1 text-gray-400 hover:text-gray-600">
                      <ExternalLink className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )
        })
      )}
    </div>
  )
}

interface ChunksViewProps {
  chunks: SourceInfo[]
  expandedItems: Set<string>
  onToggleExpanded: (id: string) => void
}

function ChunksView({ chunks, expandedItems, onToggleExpanded }: ChunksViewProps) {
  return (
    <div className="p-4 space-y-3">
      {chunks.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          <Eye className="h-8 w-8 mx-auto mb-2 text-gray-400" />
          <p>No sources retrieved</p>
          <p className="text-sm">Ask a question to see retrieved content</p>
        </div>
      ) : (
        chunks.map((chunk, index) => {
          const itemId = `chunk-${index}`
          const isExpanded = expandedItems.has(itemId)
          
          return (
            <div key={index} className="border border-gray-200 rounded-lg overflow-hidden">
              <div className="p-3">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500">
                      Source {index + 1}
                    </span>
                    <span className="text-xs text-gray-500">
                      • {chunk.document}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="text-xs text-gray-500">
                      Score: {(chunk.score * 100).toFixed(0)}%
                    </div>
                    <button
                      onClick={() => onToggleExpanded(itemId)}
                      className="p-1 text-gray-400 hover:text-gray-600"
                    >
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
                
                <p className="text-sm text-gray-700">
                  {isExpanded ? chunk.content : `${chunk.content.slice(0, 200)}...`}
                </p>
              </div>
            </div>
          )
        })
      )}
    </div>
  )
}
