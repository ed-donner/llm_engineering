'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, User, Bot } from 'lucide-react'
import { useSubmitQuery, conversationKeys, useConversationDetail, useGenerateConversationTitle } from '@/hooks/api'
import { useQueryClient } from '@tanstack/react-query'
import { cn } from '@/lib/utils'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import type { ChatMessage, StreamingQueryResponse, Citation, SourceInfo } from '@/types'

interface ChatViewProps {
  sessionId?: string
  onSourcesUpdate?: (sources: SourceInfo[], citations: Citation[]) => void
}

export function ChatView({ sessionId: externalSessionId, onSourcesUpdate }: ChatViewProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [currentSessionId, setCurrentSessionId] = useState<string>(() => 
    externalSessionId || `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  )
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const isProcessingQuery = useRef(false) // Track if we're processing a query
  const processingSessionId = useRef<string | null>(null) // Track which session is processing
  const processingMessages = useRef<ChatMessage[]>([]) // Store messages for processing session
  const processingStreamingContent = useRef<string>('') // Store streaming content
  
  const submitQuery = useSubmitQuery()
  const queryClient = useQueryClient()
  const generateTitle = useGenerateConversationTitle()
  
  // Update sessionId when externalSessionId changes, or create new one when undefined
  useEffect(() => {
    console.log('📌 Session change effect:', {
      externalSessionId,
      currentSessionId,
      isProcessing: isProcessingQuery.current,
      processingSession: processingSessionId.current
    })
    
    if (externalSessionId) {
      // Only clear if switching to a DIFFERENT existing session
      if (externalSessionId !== currentSessionId) {
        console.log('🔄 Switching to different session:', externalSessionId)
        
        // If we're switching FROM a processing session, save its state
        if (isProcessingQuery.current && processingSessionId.current === currentSessionId) {
          processingMessages.current = messages
          processingStreamingContent.current = streamingContent
          console.log('💾 Saved processing session state:', messages.length, 'messages')
        }
        
        setCurrentSessionId(externalSessionId)
        
        // If we're switching TO the processing session, restore its state
        if (processingSessionId.current === externalSessionId) {
          console.log('⚡ Restoring processing session UI:', processingMessages.current.length, 'messages')
          setMessages(processingMessages.current)
          setStreamingContent(processingStreamingContent.current)
          setIsStreaming(true)
        } else {
          // Normal session switch - clear everything
          setMessages([])
          setStreamingContent('')
          setIsStreaming(false)
        }
        // DON'T reset processing flags - let them persist so the guard works when switching back
      }
    } else {
      // Generate new session ID when externalSessionId becomes undefined (new chat)
      const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      console.log('✨ Creating new chat session:', newSessionId)
      setCurrentSessionId(newSessionId)
      // Clear messages for new chat
      setMessages([])
      setStreamingContent('')
      setIsStreaming(false)
      // Only reset if starting a completely new chat (not switching between existing ones)
      if (!isProcessingQuery.current) {
        processingSessionId.current = null
      }
    }
  }, [externalSessionId])
  
  // Load conversation history if sessionId is provided
  const { data: conversationData } = useConversationDetail(currentSessionId)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent])

  // Load conversation history when data is fetched
  useEffect(() => {
    console.log('🔍 History load effect triggered:', {
      isProcessing: isProcessingQuery.current,
      processingSession: processingSessionId.current,
      currentSession: currentSessionId,
      conversationDataExists: !!conversationData,
      turnCount: conversationData?.turn_count
    })
    
    // Don't replace messages if we're currently processing a query for THIS session
    if (isProcessingQuery.current && processingSessionId.current === currentSessionId) {
      console.log('⏸️ Skipping history load - query in progress for this session')
      return
    }
    
    if (conversationData?.turns && conversationData.turns.length > 0) {
      const loadedMessages: ChatMessage[] = []
      conversationData.turns.forEach((turn: any) => {
        // Add user message
        loadedMessages.push({
          id: `user-${turn.turn_id}`,
          role: 'user',
          content: turn.query,
          timestamp: turn.timestamp
        })
        // Add assistant message
        loadedMessages.push({
          id: `assistant-${turn.turn_id}`,
          role: 'assistant',
          content: turn.response,
          timestamp: turn.timestamp,
          citations: turn.sources || []
        })
      })
      
      // Only update if loaded messages count is different from current
      if (loadedMessages.length !== messages.length) {
        console.log('📥 Loading conversation history:', loadedMessages.length, 'messages')
        setMessages(loadedMessages)
      }
    } else if (conversationData && conversationData.turn_count === 0) {
      // Session exists but has no turns yet - don't clear existing messages
      console.log('Session exists with no turns, keeping current messages')
    }
  }, [conversationData])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || submitQuery.isPending) return

    // Check if this is the first message BEFORE adding it
    const isFirstMessage = messages.length === 0
    
    // Mark that we're processing a query for this session
    isProcessingQuery.current = true
    processingSessionId.current = currentSessionId
    console.log('🚀 Starting query processing for session:', currentSessionId)

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    const queryText = input.trim()
    setInput('')
    setIsStreaming(true)
    setStreamingContent('')

    // Invalidate conversations cache
    queryClient.invalidateQueries({ queryKey: conversationKeys.all })

    try {
      const response = await submitQuery.mutateAsync({
        query: queryText,
        sessionId: currentSessionId,
        onStreamingStart: () => {
          console.log('🚀 Streaming started')
          // Refetch conversations now that session is confirmed created
          queryClient.refetchQueries({ queryKey: conversationKeys.all })
        },
        onStreamToken: (token: string) => {
          setStreamingContent(prev => prev + token)
        },
        onStreamingEnd: () => {
          console.log('✅ Streaming ended')
        }
      })

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString(),
        citations: response.citations,
        query_id: response.query_id
      }

      setMessages(prev => [...prev, assistantMessage])

      // Update sources panel with the response data
      console.log('📝 ChatView: Response received:', {
        chunks: response.chunks,
        citations: response.citations,
        chunksLength: response.chunks?.length,
        citationsLength: response.citations?.length
      })
      
      if (onSourcesUpdate) {
        onSourcesUpdate(response.chunks || [], response.citations || [])
        console.log('📡 ChatView: Called onSourcesUpdate with:', response.chunks?.length, 'sources and', response.citations?.length, 'citations')
      }

      // Invalidate conversations cache again to update turn count
      queryClient.invalidateQueries({ queryKey: conversationKeys.all })
      
      // Auto-generate title after first turn
      console.log('🔍 Checking auto-title conditions:', { 
        isFirstMessage, 
        messagesLength: messages.length,
        currentSessionId 
      })
      
      if (isFirstMessage) {
        console.log('🎯 This is the first message! Auto-generating title for:', currentSessionId)
        // Add a delay to ensure the turn is saved to backend first
        setTimeout(async () => {
          try {
            console.log('⏱️ Attempting to generate title now...')
            const result = await generateTitle.mutateAsync(currentSessionId)
            console.log('✅ Title generated successfully:', result)
          } catch (error) {
            console.error('❌ Failed to auto-generate title:', error)
            // Don't block user on title generation failure
          }
        }, 3000) // 3 seconds to ensure backend saves the turn
      } else {
        console.log('❌ Not first message, skipping auto-title. messagesLength:', messages.length)
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your query. Please try again.',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsStreaming(false)
      setStreamingContent('')
      // Mark query processing as complete
      console.log('✅ Query processing complete for session:', currentSessionId)
      isProcessingQuery.current = false
      processingSessionId.current = null
      processingMessages.current = []
      processingStreamingContent.current = ''
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [input])

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 min-h-0">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Bot className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium mb-2" style={{ color: '#000000' }}>
              Welcome to Local RAG
            </h3>
            <p className="text-gray-500 max-w-md">
              Ask questions about your uploaded documents. I'll search through them 
              and provide detailed answers with citations.
            </p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isStreaming && (
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-blue-600" />
                  </div>
                </div>
                <div className="flex-1">
                  <div className="bg-white rounded-lg border border-gray-200 px-4 py-3">
                    {streamingContent ? (
                      <div className="prose prose-sm max-w-none text-gray-900 dark:text-gray-100">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm, remarkMath]}
                          rehypePlugins={[rehypeKatex]}
                          components={{
                            p: ({ children }) => <p className="mb-2 last:mb-0 text-gray-900 dark:text-gray-100">{children}</p>,
                            strong: ({ children }) => <strong className="font-bold text-gray-900 dark:text-gray-100">{children}</strong>,
                            ul: ({ children }) => <ul className="list-disc pl-4 mb-2 text-gray-900 dark:text-gray-100">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 text-gray-900 dark:text-gray-100">{children}</ol>,
                            li: ({ children }) => <li className="mb-1 text-gray-900 dark:text-gray-100">{children}</li>,
                            h1: ({ children }) => <h1 className="text-xl font-bold mb-3 text-gray-900 dark:text-gray-100">{children}</h1>,
                            h2: ({ children }) => <h2 className="text-lg font-bold mb-2 text-gray-900 dark:text-gray-100">{children}</h2>,
                            h3: ({ children }) => <h3 className="text-base font-bold mb-2 text-gray-900 dark:text-gray-100">{children}</h3>,
                            code: ({ children }) => <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded text-gray-900 dark:text-gray-100 font-mono text-sm">{children}</code>,
                            blockquote: ({ children }) => <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 italic text-gray-700 dark:text-gray-300">{children}</blockquote>
                          }}
                        >
                          {streamingContent}
                        </ReactMarkdown>
                        <span className="inline-block w-2 h-4 bg-blue-600 animate-pulse ml-1" />
                      </div>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                        <span className="text-sm text-gray-600">Thinking...</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white p-4">
        <form onSubmit={handleSubmit} className="flex space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents..."
              rows={1}
              className="w-full resize-none border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-3 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent max-h-32 placeholder:text-gray-500 dark:placeholder:text-gray-400"
              disabled={submitQuery.isPending}
            />
          </div>
          <button
            type="submit"
            disabled={!input.trim() || submitQuery.isPending}
            className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
          >
            {submitQuery.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </form>
      </div>
    </div>
  )
}

interface MessageBubbleProps {
  message: ChatMessage
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={cn(
      'flex space-x-3',
      isUser ? 'flex-row-reverse space-x-reverse' : ''
    )}>
      {/* Avatar */}
      <div className="flex-shrink-0">
        <div className={cn(
          'h-8 w-8 rounded-full flex items-center justify-center',
          isUser ? 'bg-gray-200' : 'bg-blue-100'
        )}>
          {isUser ? (
            <User className="h-4 w-4 text-gray-600" />
          ) : (
            <Bot className="h-4 w-4 text-blue-600" />
          )}
        </div>
      </div>

      {/* Message Content */}
      <div className="flex-1 max-w-3xl">
        <div className={cn(
          'rounded-lg px-4 py-3',
          isUser 
            ? 'bg-blue-600 text-white ml-auto'
            : 'bg-white border border-gray-200'
        )}>
          <div className="prose prose-sm max-w-none">
            {isUser ? (
              // For user messages, keep simple text formatting
              (message.content || '').split('\n').map((line, index) => (
                <p key={index} className={cn(
                  'mb-2 last:mb-0',
                  'text-white !text-white'
                )} style={{ color: 'white' }}>
                  {line}
                </p>
              ))
            ) : (
              // For assistant messages, render markdown
              <div className="text-gray-900 dark:text-gray-100">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                  components={{
                    p: ({ children }) => <p className="mb-2 last:mb-0 text-gray-900 dark:text-gray-100">{children}</p>,
                    strong: ({ children }) => <strong className="font-bold text-gray-900 dark:text-gray-100">{children}</strong>,
                    ul: ({ children }) => <ul className="list-disc pl-4 mb-2 text-gray-900 dark:text-gray-100">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 text-gray-900 dark:text-gray-100">{children}</ol>,
                    li: ({ children }) => <li className="mb-1 text-gray-900 dark:text-gray-100">{children}</li>,
                    h1: ({ children }) => <h1 className="text-xl font-bold mb-3 text-gray-900 dark:text-gray-100">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-lg font-bold mb-2 text-gray-900 dark:text-gray-100">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-base font-bold mb-2 text-gray-900 dark:text-gray-100">{children}</h3>,
                    code: ({ children }) => <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded text-gray-900 dark:text-gray-100 font-mono text-sm">{children}</code>,
                    blockquote: ({ children }) => <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 italic text-gray-700 dark:text-gray-300">{children}</blockquote>
                  }}
                >
                  {message.content || ''}
                </ReactMarkdown>
              </div>
            )}
          </div>
        </div>

        {/* Timestamp */}
        <div className={cn(
          'text-xs text-gray-500 mt-1',
          isUser ? 'text-right' : 'text-left'
        )}>
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}
