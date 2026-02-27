import React from 'react'
import './StatusIndicator.css'

export default function StatusIndicator({ status, callId, agentId }) {
  const getStatusColor = () => {
    switch (status) {
      case 'connected':
        return '#4caf50'
      case 'recording':
        return '#f44336'
      case 'error':
        return '#ff9800'
      default:
        return '#9e9e9e'
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'connected':
        return 'Connected'
      case 'recording':
        return 'Recording'
      case 'error':
        return 'Error'
      default:
        return 'Disconnected'
    }
  }

  return (
    <div className="status-indicator">
      <div 
        className="status-dot" 
        style={{ backgroundColor: getStatusColor() }}
      />
      <span className="status-text">{getStatusText()}</span>
      <div className="status-info">
        <span className="info-item">Call: {callId.slice(0, 8)}...</span>
        <span className="info-item">Agent: {agentId}</span>
      </div>
    </div>
  )
}
