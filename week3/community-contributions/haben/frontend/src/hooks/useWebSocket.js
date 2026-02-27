import { useEffect, useRef, useState } from 'react'

export function useWebSocket({ url, onMessage, onOpen, onError, onClose }) {
  const [ws, setWs] = useState(null)
  const [readyState, setReadyState] = useState(WebSocket.CLOSED)
  const reconnectTimeoutRef = useRef(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  useEffect(() => {
    let websocket = null
    let isMounted = true

    const connect = () => {
      try {
        websocket = new WebSocket(url)
        setWs(websocket)
        setReadyState(websocket.readyState)

        websocket.onopen = () => {
          if (isMounted) {
            setReadyState(WebSocket.OPEN)
            reconnectAttempts.current = 0
            if (onOpen) onOpen(websocket)
          }
        }

        websocket.onmessage = (event) => {
          if (isMounted && onMessage) {
            try {
              const data = JSON.parse(event.data)
              onMessage(data)
            } catch (e) {
              // Handle non-JSON messages
              onMessage(event.data)
            }
          }
        }

        websocket.onerror = (error) => {
          if (isMounted) {
            setReadyState(websocket.readyState)
            if (onError) onError(error)
          }
        }

        websocket.onclose = () => {
          if (isMounted) {
            setReadyState(WebSocket.CLOSED)
            if (onClose) onClose()

            // Attempt to reconnect
            if (reconnectAttempts.current < maxReconnectAttempts) {
              reconnectAttempts.current++
              const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
              reconnectTimeoutRef.current = setTimeout(() => {
                if (isMounted) connect()
              }, delay)
            }
          }
        }
      } catch (error) {
        if (isMounted && onError) onError(error)
      }
    }

    connect()

    return () => {
      isMounted = false
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (websocket) {
        websocket.close()
      }
    }
  }, [url])

  const send = (data) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      if (typeof data === 'string') {
        ws.send(data)
      } else {
        ws.send(JSON.stringify(data))
      }
    } else {
      console.warn('WebSocket is not open')
    }
  }

  return { ws, readyState, send }
}
