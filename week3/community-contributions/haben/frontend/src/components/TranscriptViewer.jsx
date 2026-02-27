import React, { useEffect, useRef } from 'react'
import './TranscriptViewer.css'

export default function TranscriptViewer({ transcript, callId }) {
  const transcriptEndRef = useRef(null)

  useEffect(() => {
    // Auto-scroll to bottom when new transcript arrives
    if (transcriptEndRef.current) {
      transcriptEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [transcript])

  if (!transcript || transcript.length === 0) {
    return (
      <div className="transcript-viewer">
        <div className="transcript-header">
          <h2>Live Transcript</h2>
        </div>
        <div className="transcript-empty">
          <p>No transcript available yet.</p>
          <p className="empty-hint">Start recording to begin transcription.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="transcript-viewer">
      <div className="transcript-header">
        <h2>Live Transcript</h2>
        <span className="chunk-count">{transcript.length} chunks</span>
      </div>
      <div className="transcript-content">
        {transcript.map((chunk, index) => (
          <div key={index} className="transcript-chunk">
            <div className="chunk-header">
              <span className="speaker-label">{chunk.speaker || 'UNKNOWN'}</span>
              <span className="chunk-time">
                {chunk.start_time ? new Date(chunk.start_time).toLocaleTimeString() : ''}
              </span>
            </div>
            <div className="chunk-text">{chunk.text || chunk.original_text || ''}</div>
            {chunk.cleaned_text && chunk.cleaned_text !== chunk.text && (
              <div className="chunk-cleaned">
                <small>Cleaned: {chunk.cleaned_text}</small>
              </div>
            )}
          </div>
        ))}
        <div ref={transcriptEndRef} />
      </div>
    </div>
  )
}
