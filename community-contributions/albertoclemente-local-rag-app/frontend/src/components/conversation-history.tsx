'use client'

import { useState } from 'react'
import { 
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  Trash2,
  Search,
  Clock,
  MessageCircle,
  Sparkles,
  Plus
} from 'lucide-react'
import { useConversations, useDeleteConversation, useGenerateConversationTitle } from '@/hooks/api'
import { cn, formatTimestamp } from '@/lib/utils'

interface ConversationHistoryProps {
  isOpen: boolean
  onToggle: () => void
  onSelectConversation?: (sessionId: string) => void
  onNewChat?: () => void
  currentSessionId?: string
}

export function ConversationHistory({ 
  isOpen, 
  onToggle, 
  onSelectConversation,
  onNewChat,
  currentSessionId 
}: ConversationHistoryProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const { data: conversationsData, isLoading } = useConversations()
  const deleteConversation = useDeleteConversation()
  const generateTitle = useGenerateConversationTitle()

  const conversations = conversationsData?.sessions || []

  // Filter conversations based on search
  const filteredConversations = conversations.filter((conv: any) => {
    if (!searchQuery) return true
    const searchLower = searchQuery.toLowerCase()
    return (
      conv.session_id?.toLowerCase().includes(searchLower) ||
      conv.title?.toLowerCase().includes(searchLower)
    )
  })

  const handleDelete = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm('Delete this conversation? This cannot be undone.')) {
      try {
        await deleteConversation.mutateAsync(sessionId)
      } catch (error) {
        console.error('Failed to delete conversation:', error)
      }
    }
  }

  const handleGenerateTitle = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await generateTitle.mutateAsync(sessionId)
    } catch (error) {
      console.error('Failed to generate title:', error)
    }
  }

  if (!isOpen) {
    return (
      <div className="h-full flex flex-col items-center py-4 bg-white border-r border-gray-200">
        <button
          onClick={onToggle}
          className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg mb-4"
          aria-label="Expand sidebar"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
        
        <div className="space-y-2">
          <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg">
            <MessageSquare className="h-5 w-5" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-white border-r border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center">
            <MessageSquare className="h-5 w-5 mr-2 text-blue-600" />
            Conversations
          </h2>
          <div className="flex items-center space-x-1">
            <button
              onClick={() => onNewChat?.()}
              className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              aria-label="New chat"
              title="Start new chat"
            >
              <Plus className="h-5 w-5" />
            </button>
            <button
              onClick={onToggle}
              className="p-1 text-gray-500 hover:bg-gray-100 rounded-lg"
              aria-label="Collapse sidebar"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-gray-500">
            <div className="animate-spin h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-2" />
            <p className="text-sm">Loading conversations...</p>
          </div>
        ) : filteredConversations.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <MessageCircle className="h-8 w-8 mx-auto mb-2 text-gray-400" />
            <p className="text-sm font-medium">No conversations yet</p>
            <p className="text-xs mt-1">Start chatting to see your history here</p>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {filteredConversations.map((conv: any) => {
              const isActive = conv.session_id === currentSessionId
              const lastActive = new Date(conv.last_active)
              const created = new Date(conv.created_at)
              
              return (
                <div
                  key={conv.session_id}
                  onClick={() => onSelectConversation?.(conv.session_id)}
                  className={cn(
                    'p-3 rounded-lg cursor-pointer transition-colors group',
                    isActive 
                      ? 'bg-blue-100 dark:bg-blue-900 border border-blue-300 dark:border-blue-700' 
                      : 'hover:bg-gray-50 dark:hover:bg-gray-700 border border-transparent'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <MessageSquare className={cn(
                          'h-4 w-4 flex-shrink-0',
                          isActive ? 'text-blue-600' : 'text-gray-400'
                        )} />
                        <span className="text-sm font-medium text-gray-900 truncate">
                          {conv.title || (conv.turn_count === 0 ? 'New Chat' : `Session ${conv.session_id.split('-')[0]}`)}
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-2 text-xs text-gray-500 mb-1">
                        <Clock className="h-3 w-3" />
                        <span>{formatTimestamp(conv.last_active)}</span>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          {conv.turn_count} {conv.turn_count === 1 ? 'turn' : 'turns'}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex flex-col space-y-1">
                      {!conv.title && (
                        <button
                          onClick={(e) => handleGenerateTitle(conv.session_id, e)}
                          className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                          aria-label="Generate title"
                          title="Generate AI title"
                        >
                          <Sparkles className="h-4 w-4" />
                        </button>
                      )}
                      <button
                        onClick={(e) => handleDelete(conv.session_id, e)}
                        className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                        aria-label="Delete conversation"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Footer Stats */}
      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500 space-y-1">
          <div className="flex justify-between">
            <span>Total conversations:</span>
            <span className="font-medium text-gray-700">{conversations.length}</span>
          </div>
          {conversations.length > 0 && (
            <div className="flex justify-between">
              <span>Total turns:</span>
              <span className="font-medium text-gray-700">
                {conversations.reduce((sum: number, conv: any) => sum + (conv.turn_count || 0), 0)}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
