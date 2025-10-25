'use client'

import React, { useState } from 'react'
import { Settings, Info, Brain } from 'lucide-react'
import { useSettings, useSystemStatus } from '@/hooks/api'
import { cn } from '@/lib/utils'
import { SettingsModal } from '@/components/settings-modal'

interface AppHeaderProps {
  onToggleSources: () => void
  sourcesOpen: boolean
}

export function AppHeader({ onToggleSources, sourcesOpen }: AppHeaderProps) {
  const [settingsOpen, setSettingsOpen] = useState(false)
  const { data: settings, isLoading: settingsLoading } = useSettings()
  const { data: status, isLoading: statusLoading } = useSystemStatus()

  // Debug settings modal state
  React.useEffect(() => {
    console.log('⚙️ Settings modal state changed:', settingsOpen)
  }, [settingsOpen])

  const getStatusColor = () => {
    if (statusLoading || !status) return 'bg-gray-500'
    switch (status.status) {
      case 'operational':
        return 'bg-green-500'
      case 'degraded':
        return 'bg-yellow-500'
      case 'offline':
      case 'error':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getProfileBadgeColor = () => {
    if (settingsLoading || !settings) return 'bg-gray-100 text-gray-800'
    switch (settings.rag_profile) {
      case 'eco':
        return 'bg-green-100 text-green-800'
      case 'balanced':
        return 'bg-blue-100 text-blue-800'
      case 'performance':
        return 'bg-purple-100 text-purple-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = () => {
    if (statusLoading) return 'connecting...'
    return status?.status || 'connecting...'
  }

  const getProfileText = () => {
    if (settingsLoading) return 'loading...'
    return settings?.rag_profile || 'balanced'
  }

  return (
    <>
      <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      {/* Left Side - Logo and Title */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <Brain className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-xl font-bold text-gray-900">Local RAG</h1>
            <div className="flex items-center space-x-2">
              <div className={cn('w-2 h-2 rounded-full', getStatusColor())} />
              <span className="text-xs text-gray-500">
                {getStatusText()}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Center - Model and Profile Info */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Model:</span>
          <span className="text-sm font-medium text-gray-900">{status?.model_name || 'local-llm'}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Profile:</span>
          <span className={cn(
            'px-2 py-1 rounded-full text-xs font-medium',
            getProfileBadgeColor()
          )}>
            {getProfileText()}
          </span>
        </div>
      </div>

      {/* Right Side - Action Buttons */}
      <div className="flex items-center space-x-2">
        <button
          onClick={onToggleSources}
          className={cn(
            'p-2 rounded-lg transition-colors',
            sourcesOpen
              ? 'bg-blue-100 text-blue-600'
              : 'text-gray-500 hover:bg-gray-100'
          )}
          title="Toggle Documents Panel"
        >
          <Info className="h-5 w-5" />
        </button>
        
                <button
          onClick={() => {
            console.log('⚙️ Settings button clicked!')
            alert('Settings button clicked! Check console for details.')
            setSettingsOpen(true)
          }}
          className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
          title="Settings"
        >
          <Settings className="h-5 w-5" />
        </button>
      </div>
    </header>

    {/* Settings Modal */}
    {settingsOpen && (
      <SettingsModal 
        isOpen={settingsOpen} 
        onClose={() => setSettingsOpen(false)} 
      />
    )}
  </>
  )
}
