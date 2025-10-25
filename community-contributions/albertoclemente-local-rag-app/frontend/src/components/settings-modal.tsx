'use client'

import React, { useState } from 'react'
import { X, Save, RotateCcw } from 'lucide-react'
import { useSettings, useUpdateSettings } from '@/hooks/api'
import { cn } from '@/lib/utils'
import type { Settings } from '@/types'
import { useThemeContext } from '@/components/providers'
import type { Theme } from '@/lib/theme'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const { data: currentSettings, isLoading } = useSettings()
  const updateSettings = useUpdateSettings()
  const { theme, setTheme } = useThemeContext()
  const [formData, setFormData] = useState<Settings>({
    rag_profile: 'balanced',
    chunk_size: 1000,
    chunk_overlap: 200,
    retrieval_k: 5,
    min_relevance_score: 0.0,
    llm_temperature: 0.7,
    max_tokens: 2048,
    system_prompt: ''
  })

  // Update form data when settings load
  React.useEffect(() => {
    if (currentSettings) {
      setFormData(currentSettings)
    }
  }, [currentSettings])

  const handleInputChange = (field: keyof Settings, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync(formData)
      onClose()
    } catch (error) {
      console.error('Error saving settings:', error)
    }
  }

  const handleReset = () => {
    if (currentSettings) {
      setFormData(currentSettings)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Debug indicator */}
      <div className="fixed top-4 right-4 z-[60] bg-green-500 text-white px-2 py-1 rounded text-xs">
        Settings Modal Open
      </div>
      
      <div className="flex min-h-screen items-center justify-center px-4 py-6">
        {/* Backdrop */}
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={onClose}
        />
        
        {/* Modal */}
        <div className="relative bg-[var(--bg-elev)] text-[var(--text-primary)] rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-color)]">
            <h2 className="text-xl font-semibold">Settings</h2>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Content */}
          <div className="px-6 py-4 overflow-y-auto max-h-[60vh]">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Theme */}
                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">Theme</label>
                  <select
                    value={theme}
                    onChange={(e) => setTheme(e.target.value as Theme)}
                    className="w-full px-3 py-2 border border-[var(--border-color)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-[var(--text-primary)]"
                  >
                    <option value="light">Light</option>
                    <option value="dark">Dark</option>
                  </select>
                </div>
                {/* RAG Profile */}
                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                    RAG Profile
                  </label>
                  <select
                    value={formData.rag_profile}
                    onChange={(e) => handleInputChange('rag_profile', e.target.value as 'eco' | 'balanced' | 'performance')}
                    className="w-full px-3 py-2 border border-[var(--border-color)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-[var(--text-primary)]"
                  >
                    <option value="eco">Eco - Fast, lower accuracy</option>
                    <option value="balanced">Balanced - Good speed and accuracy</option>
                    <option value="performance">Performance - Slower, higher accuracy</option>
                  </select>
                </div>

                {/* Chunking Settings */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                      Chunk Size
                    </label>
                    <input
                      type="number"
                      value={formData.chunk_size}
                      onChange={(e) => handleInputChange('chunk_size', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-[var(--border-color)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-[var(--text-primary)]"
                      min="100"
                      max="4000"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                      Chunk Overlap
                    </label>
                    <input
                      type="number"
                      value={formData.chunk_overlap}
                      onChange={(e) => handleInputChange('chunk_overlap', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-[var(--border-color)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-[var(--text-primary)]"
                      min="0"
                      max="1000"
                    />
                  </div>
                </div>

                {/* Retrieval Settings */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                      Retrieval K
                    </label>
                    <input
                      type="number"
                      value={formData.retrieval_k}
                      onChange={(e) => handleInputChange('retrieval_k', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-[var(--border-color)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-[var(--text-primary)]"
                      min="1"
                      max="20"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                      Min Relevance Score
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.min_relevance_score}
                      onChange={(e) => handleInputChange('min_relevance_score', parseFloat(e.target.value))}
                      className="w-full px-3 py-2 border border-[var(--border-color)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-[var(--text-primary)]"
                      min="0"
                      max="1"
                    />
                  </div>
                </div>

                {/* LLM Settings */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                      Temperature
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.llm_temperature}
                      onChange={(e) => handleInputChange('llm_temperature', parseFloat(e.target.value))}
                      className="w-full px-3 py-2 border border-[var(--border-color)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-[var(--text-primary)]"
                      min="0"
                      max="2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                      Max Tokens
                    </label>
                    <input
                      type="number"
                      value={formData.max_tokens}
                      onChange={(e) => handleInputChange('max_tokens', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-[var(--border-color)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-[var(--text-primary)]"
                      min="100"
                      max="8192"
                    />
                  </div>
                </div>

                {/* System Prompt */}
                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                    System Prompt (Optional)
                  </label>
                  <textarea
                    value={formData.system_prompt || ''}
                    onChange={(e) => handleInputChange('system_prompt', e.target.value)}
                    className="w-full px-3 py-2 border border-[var(--border-color)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-[var(--text-primary)]"
                    rows={4}
                    placeholder="Custom system prompt for the LLM..."
                  />
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-[var(--border-color)] bg-[var(--bg-elev)]">
            <button
              onClick={handleReset}
              className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <RotateCcw className="h-4 w-4" />
              <span>Reset</span>
            </button>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={updateSettings.isPending}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed rounded-lg transition-colors"
              >
                {updateSettings.isPending ? (
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                <span>{updateSettings.isPending ? 'Saving...' : 'Save Changes'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}