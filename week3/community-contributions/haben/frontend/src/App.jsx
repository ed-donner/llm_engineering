import React, { useState, useEffect, useCallback } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { useAudioCapture } from './hooks/useAudioCapture'
import TranscriptViewer from './components/TranscriptViewer'
import SummaryPanel from './components/SummaryPanel'
import ActionItemsPanel from './components/ActionItemsPanel'
import AudioControls from './components/AudioControls'
import StatusIndicator from './components/StatusIndicator'
import './App.css'

function App() {
  const [callId] = useState(() => {
    // Generate or retrieve call ID
    const stored = sessionStorage.getItem('callId')
    if (stored) return stored
    const newId = crypto.randomUUID()
    sessionStorage.setItem('callId', newId)
    return newId
  })
  
  const [agentId] = useState(() => {
    const stored = sessionStorage.getItem('agentId')
    if (stored) return stored
    const newId = `agent_${Date.now()}`
    sessionStorage.setItem('agentId', newId)
    return newId
  })

  const [transcript, setTranscript] = useState([])
  const [llmData, setLlmData] = useState(null)
  const [isRecording, setIsRecording] = useState(false)
  // Start with 'connecting' to enable button while WebSocket is connecting
  const [connectionStatus, setConnectionStatus] = useState('connecting')
  
  // Debug: Log connection status changes
  useEffect(() => {
    console.log('Connection status changed:', connectionStatus, 'isRecording:', isRecording)
  }, [connectionStatus, isRecording])

  // WebSocket for audio chunks
  const audioWs = useWebSocket({
    url: `ws://localhost:8000/ws/call`,
    onMessage: (data) => {
      console.log('WebSocket message received:', data)
      if (data.type === 'chunk_acknowledged') {
        console.log('Chunk acknowledged:', data.chunk_index)
      } else if (data.type === 'session_started') {
        setConnectionStatus('connected')
        console.log('Session started:', data)
      }
    },
    onOpen: (ws) => {
      console.log('WebSocket opened, setting status to connected')
      // Set connection status to connected when WebSocket opens
      setConnectionStatus('connected')
      // Send session setup - small delay to ensure connection is fully ready
      setTimeout(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          try {
            console.log('Sending session setup message')
            ws.send(JSON.stringify({
              call_id: callId,
              agent_id: agentId,
              action: 'start'
            }))
          } catch (error) {
            console.error('Error sending session setup:', error)
          }
        } else {
          console.warn('WebSocket not open when trying to send session setup')
        }
      }, 100)
    },
    onError: (error) => {
      console.error('Audio WebSocket error:', error)
      setConnectionStatus('error')
      // Don't disable button on error - allow retry
    },
    onClose: () => {
      // Only set to disconnected if not currently recording
      if (!isRecording) {
        setConnectionStatus('disconnected')
      }
    }
  })

  // WebSocket for LLM updates
  const llmWs = useWebSocket({
    url: `ws://localhost:8000/ws/llm-updates/${callId}`,
    onMessage: (data) => {
      if (data.type === 'llm_update') {
        setLlmData(data.data)
        console.log('LLM update received:', data.data)
      }
    },
    onError: (error) => {
      console.error('LLM WebSocket error:', error)
    }
  })

  // Audio capture hook
  const {
    startRecording,
    stopRecording,
    isCapturing,
    error: audioError
  } = useAudioCapture({
    onAudioChunk: (audioData, chunkIndex) => {
      // Send audio chunk to WebSocket
      if (audioWs.ws && audioWs.ws.readyState === WebSocket.OPEN) {
        try {
          const base64Audio = btoa(
            String.fromCharCode(...new Uint8Array(audioData))
          )
          
          const message = {
            type: 'audio_chunk',
            audio_data: base64Audio,
            chunk_index: chunkIndex,
            timestamp: Date.now() / 1000,
            format: 'pcm',
            sample_rate: 16000,
            channels: 1
          }
          
          audioWs.ws.send(JSON.stringify(message))
          console.log(`Sent audio chunk ${chunkIndex}, size: ${audioData.byteLength} bytes`)
        } catch (error) {
          console.error('Error sending audio chunk:', error)
        }
      } else {
        console.warn('WebSocket not open, cannot send audio chunk')
      }
    },
    enabled: isRecording
  })

  // Fetch transcripts from API
  const fetchTranscripts = useCallback(async () => {
    try {
      const response = await fetch(`http://localhost:8000/transcripts/${callId}`)
      if (response.ok) {
        const data = await response.json()
        setTranscript(data.transcripts || [])
      }
    } catch (error) {
      console.error('Error fetching transcripts:', error)
    }
  }, [callId])
  
  // Fetch transcripts periodically when recording
  useEffect(() => {
    if (isRecording) {
      const interval = setInterval(fetchTranscripts, 2000) // Poll every 2 seconds
      return () => clearInterval(interval)
    }
  }, [isRecording, fetchTranscripts])

  const handleStartRecording = async () => {
    try {
      await startRecording()
      setIsRecording(true)
      setConnectionStatus('recording')
    } catch (error) {
      console.error('Failed to start recording:', error)
      setConnectionStatus('error')
    }
  }

  const handleStopRecording = async () => {
    stopRecording()
    setIsRecording(false)
    setConnectionStatus('connected')
    
    // Send stop control message
    if (audioWs.ws && audioWs.ws.readyState === WebSocket.OPEN) {
      audioWs.ws.send(JSON.stringify({
        type: 'control',
        action: 'stop',
        call_id: callId,
        agent_id: agentId
      }))
    }
    
    // Wait a bit for processing, then fetch transcripts
    setTimeout(() => {
      fetchTranscripts()
    }, 3000)  // Wait 3 seconds for processing to complete
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Call Center AI Dashboard</h1>
        <StatusIndicator 
          status={connectionStatus}
          callId={callId}
          agentId={agentId}
        />
      </header>

      <div className="app-content">
        <div className="main-panel">
          <AudioControls
            isRecording={isRecording}
            onStart={handleStartRecording}
            onStop={handleStopRecording}
            disabled={false}
          />

          {audioError && (
            <div className="error-message">
              Audio Error: {audioError}
            </div>
          )}

          <TranscriptViewer
            transcript={transcript}
            callId={callId}
          />
        </div>

        <div className="sidebar">
          <SummaryPanel data={llmData} />
          <ActionItemsPanel 
            data={llmData}
            callId={callId}
          />
        </div>
      </div>
    </div>
  )
}

export default App
