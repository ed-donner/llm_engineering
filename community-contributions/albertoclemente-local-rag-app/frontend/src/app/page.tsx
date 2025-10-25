'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { AppHeader } from '@/components/app-header'
import { ConversationHistory } from '@/components/conversation-history'
import { ChatView } from '@/components/chat-view'
import { DocumentsPanel } from '@/components/documents-panel'
import { StatusBar } from '@/components/status-bar'
import type { Citation, SourceInfo } from '@/types'

export default function HomePage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [documentsOpen, setDocumentsOpen] = useState(true)
  const [currentSessionId, setCurrentSessionId] = useState<string>()

  const handleNewChat = () => {
    setCurrentSessionId(undefined)
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar - Conversation History */}
      <div
        className={cn(
          'transition-all duration-300 ease-in-out',
          sidebarOpen ? 'w-80' : 'w-16'
        )}
      >
        <ConversationHistory 
          isOpen={sidebarOpen} 
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          onSelectConversation={setCurrentSessionId}
          onNewChat={handleNewChat}
          currentSessionId={currentSessionId}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <AppHeader 
          onToggleSources={() => setDocumentsOpen(!documentsOpen)}
          sourcesOpen={documentsOpen}
        />

        {/* Main Panel */}
        <div className="flex-1 flex overflow-hidden">
          {/* Chat View */}
          <div className="flex-1 flex flex-col">
            <ChatView 
              sessionId={currentSessionId}
              onSourcesUpdate={() => {}} 
            />
          </div>

          {/* Documents Panel (Right) */}
          <div
            className={cn(
              'transition-all duration-300 ease-in-out',
              documentsOpen ? 'w-96' : 'w-0 overflow-hidden'
            )}
          >
            <DocumentsPanel isOpen={documentsOpen} />
          </div>
        </div>

        {/* Status Bar */}
        <StatusBar />
      </div>
    </div>
  )
}
