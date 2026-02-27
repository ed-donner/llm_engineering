import React from 'react'
import './AudioControls.css'

export default function AudioControls({ isRecording, onStart, onStop, disabled }) {
  return (
    <div className="audio-controls">
      <button
        className={`control-button ${isRecording ? 'stop' : 'start'}`}
        onClick={isRecording ? onStop : onStart}
        disabled={disabled}
      >
        <span className="button-icon">
          {isRecording ? '⏹' : '⏺'}
        </span>
        <span className="button-text">
          {isRecording ? 'Stop Recording' : 'Start Recording'}
        </span>
      </button>
      
      {isRecording && (
        <div className="recording-indicator">
          <span className="recording-dot"></span>
          <span>Recording in progress...</span>
        </div>
      )}
    </div>
  )
}
