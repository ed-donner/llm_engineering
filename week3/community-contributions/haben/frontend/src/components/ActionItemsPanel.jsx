import React, { useState } from 'react'
import './ActionItemsPanel.css'

export default function ActionItemsPanel({ data, callId }) {
  const [actionItems, setActionItems] = useState([])
  const [annotations, setAnnotations] = useState({})

  // Update action items when LLM data changes
  React.useEffect(() => {
    if (data?.action_items) {
      setActionItems(data.action_items)
    }
  }, [data])

  const handleConfirm = (index) => {
    setAnnotations(prev => ({
      ...prev,
      [index]: {
        ...prev[index],
        confirmed: true,
        confirmedAt: new Date().toISOString()
      }
    }))
  }

  const handleAnnotate = (index, annotation) => {
    setAnnotations(prev => ({
      ...prev,
      [index]: {
        ...prev[index],
        annotation,
        annotatedAt: new Date().toISOString()
      }
    }))
  }

  const handleHighlight = (index) => {
    setAnnotations(prev => ({
      ...prev,
      [index]: {
        ...prev[index],
        highlighted: !prev[index]?.highlighted
      }
    }))
  }

  if (!actionItems || actionItems.length === 0) {
    return (
      <div className="action-items-panel">
        <div className="panel-header">
          <h3>Action Items</h3>
        </div>
        <div className="panel-empty">
          <p>No action items identified yet.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="action-items-panel">
      <div className="panel-header">
        <h3>Action Items</h3>
        <span className="items-count">{actionItems.length} items</span>
      </div>
      <div className="panel-content">
        {actionItems.map((item, index) => {
          const annotation = annotations[index] || {}
          const isHighlighted = annotation.highlighted
          const isConfirmed = annotation.confirmed

          return (
            <div
              key={index}
              className={`action-item ${isHighlighted ? 'highlighted' : ''} ${isConfirmed ? 'confirmed' : ''}`}
            >
              <div className="item-header">
                <div className="item-priority">
                  <span className={`priority-badge priority-${item.priority || 'medium'}`}>
                    {item.priority || 'medium'}
                  </span>
                </div>
                <div className="item-actions">
                  <button
                    className="action-button highlight"
                    onClick={() => handleHighlight(index)}
                    title="Highlight"
                  >
                    {isHighlighted ? '★' : '☆'}
                  </button>
                  <button
                    className="action-button confirm"
                    onClick={() => handleConfirm(index)}
                    title="Confirm"
                    disabled={isConfirmed}
                  >
                    {isConfirmed ? '✓' : '○'}
                  </button>
                </div>
              </div>
              
              <div className="item-content">
                <p className="item-text">{item.item}</p>
                {item.assignee && (
                  <div className="item-meta">
                    <span className="meta-label">Assignee:</span>
                    <span className="meta-value">{item.assignee}</span>
                  </div>
                )}
                {item.due_date && (
                  <div className="item-meta">
                    <span className="meta-label">Due:</span>
                    <span className="meta-value">{item.due_date}</span>
                  </div>
                )}
              </div>

              {annotation.annotation && (
                <div className="item-annotation">
                  <strong>Note:</strong> {annotation.annotation}
                </div>
              )}

              <div className="item-annotation-input">
                <input
                  type="text"
                  placeholder="Add annotation..."
                  onBlur={(e) => {
                    if (e.target.value) {
                      handleAnnotate(index, e.target.value)
                    }
                  }}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && e.target.value) {
                      handleAnnotate(index, e.target.value)
                      e.target.blur()
                    }
                  }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
