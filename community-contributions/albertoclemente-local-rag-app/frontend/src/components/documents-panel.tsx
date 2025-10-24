'use client'

import React, { useMemo, useState } from 'react'
import { useDocuments, useUploadDocument, useDeleteDocument, useCategories, useCategoryStatistics } from '@/hooks/api'
import { FileText, Upload, Search, Tag, MoreVertical, Trash2, RefreshCw, Plus, X, Filter } from 'lucide-react'
import { cn, formatFileSize, formatTimestamp } from '@/lib/utils'
import { CategoryList, CategoryFilter } from '@/components/category-badge'
import type { Document } from '@/types'

interface DocumentsPanelProps {
  isOpen?: boolean
}

export function DocumentsPanel({ isOpen = true }: DocumentsPanelProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTag, setSelectedTag] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [showUpload, setShowUpload] = useState(false)
  const [groupByCategory, setGroupByCategory] = useState(false)
  const fileInputRef = React.useRef<HTMLInputElement>(null)
  
  const { data: documentsData, isLoading, error } = useDocuments()
  const { data: categoriesData } = useCategories()
  const { data: categoryStats } = useCategoryStatistics()
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
      setShowUpload(false)
    } catch (error) {
      console.error('Upload failed:', error)
    }
  }

  const documents: Document[] = Array.isArray(documentsData) ? documentsData : []
  const allCategories = categoriesData?.categories?.map(c => c.name) || []

  // Filter documents
  const filteredDocuments = documents.filter((doc: Document) => {
    if (!doc) return false
    
    const matchesSearch = searchQuery === '' || 
      (doc.name || doc.filename || doc.title || '').toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesTag = selectedTag === null || (doc.tags && doc.tags.includes(selectedTag))
    
    const matchesCategory = selectedCategory === null || 
      (doc.categories && doc.categories.includes(selectedCategory))
    
    return matchesSearch && matchesTag && matchesCategory
  })

  // Group documents by category (documents without categories grouped under "Uncategorized")
  const groupedByCategory = useMemo(() => {
    if (!groupByCategory) return {} as Record<string, Document[]>
    const groups: Record<string, Document[]> = {}
    for (const doc of filteredDocuments) {
      const cats = Array.isArray(doc.categories) && doc.categories.length > 0 ? doc.categories : ['Uncategorized']
      for (const cat of cats) {
        if (!groups[cat]) groups[cat] = []
        groups[cat].push(doc)
      }
    }
    return Object.fromEntries(Object.entries(groups).sort((a, b) => a[0].localeCompare(b[0]))) as Record<string, Document[]>
  }, [filteredDocuments, groupByCategory])

  // Get all unique tags
  const allTags: string[] = Array.from(new Set(
    documents
      .filter((doc: Document) => doc && doc.tags)
      .flatMap((doc: Document) => doc.tags || [])
  ))

  if (!isOpen) {
    return null
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center">
            <FileText className="h-5 w-5 mr-2 text-blue-600 dark:text-blue-400" />
            Documents
          </h3>
          <button
            onClick={handleUploadClick}
            className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 rounded-lg transition-colors"
          >
            <Plus className="h-4 w-4 mr-1" />
            Upload
          </button>
        </div>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          accept=".pdf,.txt,.md,.doc,.docx,.pptx,.html,.htm,.png,.jpg,.jpeg,.tiff,.bmp,.asciidoc,.adoc"
          className="hidden"
        />

        {/* Search */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Category Filter */}
        {allCategories.length > 0 && (
          <div className="mb-3">
            <div className="flex items-center gap-2 mb-2">
              <Filter className="h-3.5 w-3.5 text-gray-500 dark:text-gray-400" />
              <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Categories</span>
              {selectedCategory && (
                <button
                  onClick={() => setSelectedCategory(null)}
                  className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Clear
                </button>
              )}
            </div>
            <CategoryFilter
              selectedCategory={selectedCategory}
              onCategoryChange={setSelectedCategory}
              categories={allCategories}
              className="max-h-24 overflow-y-auto"
            />
          </div>
        )}

        {/* Tags Filter */}
        {allTags.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Tag className="h-3.5 w-3.5 text-gray-500 dark:text-gray-400" />
              <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Tags</span>
            </div>
            <div className="flex flex-wrap gap-1">
              <button
                onClick={() => setSelectedTag(null)}
                className={cn(
                  'px-2 py-1 text-xs rounded-full transition-colors',
                  selectedTag === null
                    ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                )}
              >
                All
              </button>
              {allTags.map((tag) => (
                <button
                  key={tag}
                  onClick={() => setSelectedTag(tag === selectedTag ? null : tag)}
                  className={cn(
                    'px-2 py-1 text-xs rounded-full transition-colors',
                    selectedTag === tag
                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                  )}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-gray-500">
            <div className="animate-spin h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-2" />
            <p className="text-sm">Loading documents...</p>
          </div>
        ) : error ? (
          <div className="p-4 text-center text-red-600">
            <p className="text-sm">Error loading documents</p>
            <p className="text-xs mt-1">{error instanceof Error ? error.message : 'Unknown error'}</p>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <FileText className="h-8 w-8 mx-auto mb-2 text-gray-400" />
            <p className="text-sm font-medium">
              {searchQuery || selectedTag ? 'No matching documents' : 'No documents yet'}
            </p>
            <p className="text-xs mt-1">
              {searchQuery || selectedTag ? 'Try a different search or filter' : 'Upload documents to get started'}
            </p>
          </div>
        ) : (
          <div className="p-2 space-y-2">
            <div className="flex items-center justify-end pr-1">
              <label className="flex items-center space-x-2 text-xs text-gray-600 dark:text-gray-300 select-none">
                <input
                  type="checkbox"
                  checked={groupByCategory}
                  onChange={(e) => setGroupByCategory(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600"
                />
                <span>Group by category</span>
              </label>
            </div>
            {!groupByCategory && (
              <div className="space-y-1">
                {filteredDocuments.map((doc) => (
                  <DocumentCard key={doc.id} document={doc} />
                ))}
              </div>
            )}
            {groupByCategory && (
              <div className="space-y-4">
                {Object.entries(groupedByCategory).map(([cat, docs]) => (
                  <div key={cat} className="">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center space-x-2">
                        <Filter className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                        <span className="text-sm font-semibold text-gray-800 dark:text-gray-100">{cat}</span>
                      </div>
                      <span className="text-xs text-gray-500 dark:text-gray-400">{docs.length} doc{docs.length !== 1 ? 's' : ''}</span>
                    </div>
                    <div className="space-y-1">
                      {docs.map((doc) => (
                        <DocumentCard key={doc.id} document={doc} />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer Stats */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
          <div className="flex justify-between">
            <span>Total documents:</span>
            <span className="font-medium text-gray-700 dark:text-gray-300">{documents.length}</span>
          </div>
          <div className="flex justify-between">
            <span>Showing:</span>
            <span className="font-medium text-gray-700 dark:text-gray-300">{filteredDocuments.length}</span>
          </div>
          {documents.length > 0 && (
            <div className="flex justify-between">
              <span>Total size:</span>
              <span className="font-medium text-gray-700 dark:text-gray-300">
                {formatFileSize(documents.reduce((sum, doc) => sum + (doc.sizeBytes || doc.size || 0), 0))}
              </span>
            </div>
          )}
          {categoryStats && categoryStats.categorizedDocuments > 0 && (
            <>
              <div className="flex justify-between">
                <span>Categorized:</span>
                <span className="font-medium text-gray-700 dark:text-gray-300">
                  {categoryStats.categorizedDocuments} ({Math.round((categoryStats.categorizedDocuments / categoryStats.totalDocuments) * 100)}%)
                </span>
              </div>
              {categoryStats.categoryCounts && Object.keys(categoryStats.categoryCounts).length > 0 && (
                <div className="flex justify-between">
                  <span>Top category:</span>
                  <span className="font-medium text-gray-700 dark:text-gray-300 truncate ml-2">
                    {Object.entries(categoryStats.categoryCounts).sort(([,a], [,b]) => b - a)[0][0]}
                  </span>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

interface DocumentCardProps {
  document: Document
}

function DocumentCard({ document }: DocumentCardProps) {
  const [showActions, setShowActions] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const deleteDocument = useDeleteDocument()

  const handleDelete = async () => {
    try {
      await deleteDocument.mutateAsync(document.id)
      setShowDeleteConfirm(false)
    } catch (error) {
      console.error('Delete failed:', error)
    }
  }

  return (
    <div
      className="p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 hover:bg-blue-50/50 dark:hover:bg-blue-900/10 transition-all group relative"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => {
        setShowActions(false)
        setShowDeleteConfirm(false)
      }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <FileText className="h-4 w-4 text-blue-600 dark:text-blue-400 flex-shrink-0" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
              {document.title || document.filename || document.name}
            </span>
          </div>
          
          <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400 mb-2">
            <span>{(document.type || document.file_type || 'DOC').toUpperCase()}</span>
            <span>•</span>
            <span>{formatFileSize(document.sizeBytes || document.size || 0)}</span>
          </div>
          
          {/* Category Badges */}
          {document.categories && document.categories.length > 0 && (
            <div className="mb-2">
              <CategoryList
                categories={document.categories}
                subcategoriesMap={document.categorySubcategories}
                size="sm"
                maxVisible={2}
                showSubcategories={true}
              />
            </div>
          )}
          
          {document.tags && document.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-2">
              {document.tags.map((tag, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                >
                  <Tag className="h-2.5 w-2.5 mr-0.5" />
                  {tag}
                </span>
              ))}
            </div>
          )}
          
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {formatTimestamp(document.addedAt || document.upload_date)}
            </span>
            
            {(document.indexed || document.status === 'indexed') && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
                Indexed
              </span>
            )}
          </div>
        </div>
        
        {showActions && (
          <div className="relative ml-2">
            <button
              onClick={() => setShowDeleteConfirm(!showDeleteConfirm)}
              className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
              aria-label="Delete document"
            >
              <Trash2 className="h-4 w-4" />
            </button>

            {showDeleteConfirm && (
              <div className="absolute right-0 top-0 z-10 bg-white dark:bg-gray-800 border border-red-200 dark:border-red-800 rounded-lg shadow-lg p-3 w-64">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">Delete this document?</p>
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
                  This will delete the file and all associated chunks and vectors. This action cannot be undone.
                </p>
                <div className="flex space-x-2">
                  <button
                    onClick={handleDelete}
                    disabled={deleteDocument.isPending}
                    className="flex-1 px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 disabled:bg-red-400 rounded transition-colors"
                  >
                    {deleteDocument.isPending ? 'Deleting...' : 'Delete'}
                  </button>
                  <button
                    onClick={() => setShowDeleteConfirm(false)}
                    className="flex-1 px-3 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
