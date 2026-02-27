import React from 'react'
import './SummaryPanel.css'

export default function SummaryPanel({ data }) {
  if (!data) {
    return (
      <div className="summary-panel">
        <div className="panel-header">
          <h3>Summary</h3>
        </div>
        <div className="panel-empty">
          <p>Waiting for analysis...</p>
        </div>
      </div>
    )
  }

  // Handle error case
  if (data.error) {
    return (
      <div className="summary-panel">
        <div className="panel-header">
          <h3>Summary & Analysis</h3>
        </div>
        <div className="panel-content">
          <div className="summary-section">
            <h4>Running Summary</h4>
            <p className="summary-text" style={{ color: '#f44336' }}>
              Analysis failed: {data.error}
            </p>
          </div>
          {data.summary && (
            <div className="summary-section">
              <p>{data.summary}</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  const { summary, intent, complaint, sentiment, key_topics } = data

  const getSentimentColor = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive':
        return '#4caf50'
      case 'negative':
        return '#f44336'
      default:
        return '#ff9800'
    }
  }

  const getIntentColor = (intentType) => {
    const colors = {
      question: '#2196f3',
      complaint: '#f44336',
      request: '#ff9800',
      information: '#4caf50',
      support: '#9c27b0',
      other: '#9e9e9e'
    }
    return colors[intentType] || colors.other
  }

  return (
    <div className="summary-panel">
      <div className="panel-header">
        <h3>Summary & Analysis</h3>
      </div>
      <div className="panel-content">
        {summary && (
          <div className="summary-section">
            <h4>Running Summary</h4>
            <p className="summary-text">{summary}</p>
          </div>
        )}

        {intent && (
          <div className="summary-section">
            <h4>Intent</h4>
            <div 
              className="intent-badge"
              style={{ backgroundColor: getIntentColor(intent.type) }}
            >
              {intent.type || 'other'}
            </div>
            {intent.description && (
              <p className="intent-description">{intent.description}</p>
            )}
            {intent.confidence !== undefined && (
              <div className="confidence-info">
                <span>Confidence: {(intent.confidence * 100).toFixed(0)}%</span>
                <div className="confidence-bar">
                  <div 
                    className="confidence-fill"
                    style={{ width: `${(intent.confidence || 0) * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {complaint && complaint.is_complaint && (
          <div className="summary-section">
            <h4>Complaint</h4>
            <div className="complaint-info">
              <span className="complaint-type">{complaint.type}</span>
              <span 
                className="complaint-severity"
                style={{ color: complaint.severity === 'high' ? '#f44336' : '#ff9800' }}
              >
                {complaint.severity} severity
              </span>
            </div>
            {complaint.description && (
              <p className="complaint-description">{complaint.description}</p>
            )}
          </div>
        )}

        {sentiment && (
          <div className="summary-section">
            <h4>Sentiment</h4>
            <div 
              className="sentiment-badge"
              style={{ backgroundColor: getSentimentColor(sentiment) }}
            >
              {sentiment}
            </div>
          </div>
        )}

        {key_topics && key_topics.length > 0 && (
          <div className="summary-section">
            <h4>Key Topics</h4>
            <div className="topics-list">
              {key_topics.map((topic, index) => (
                <span key={index} className="topic-tag">
                  {topic}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
