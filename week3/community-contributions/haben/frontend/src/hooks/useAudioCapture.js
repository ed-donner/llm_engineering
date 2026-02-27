import { useEffect, useRef, useState } from 'react'

const CHUNK_SIZE_MS = 200 // 200ms chunks
const SAMPLE_RATE = 16000

export function useAudioCapture({ onAudioChunk, enabled = false }) {
  const [isCapturing, setIsCapturing] = useState(false)
  const [error, setError] = useState(null)
  const streamRef = useRef(null)
  const audioContextRef = useRef(null)
  const processorRef = useRef(null)
  const chunkIndexRef = useRef(0)
  const intervalRef = useRef(null)
  const isCapturingRef = useRef(false)  // Use ref to avoid stale closure

  const startRecording = async () => {
    try {
      setError(null)
      
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: SAMPLE_RATE,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      })

      streamRef.current = stream

      // Create AudioContext
      const audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: SAMPLE_RATE
      })
      audioContextRef.current = audioContext

      // Create MediaStreamSource
      const source = audioContext.createMediaStreamSource(stream)
      
      // Create ScriptProcessorNode for chunking (fallback if AudioWorklet not available)
      const bufferSize = 4096
      const processor = audioContext.createScriptProcessor(bufferSize, 1, 1)
      processorRef.current = processor

      processor.onaudioprocess = (event) => {
        if (!isCapturingRef.current) {
          return
        }

        const inputData = event.inputBuffer.getChannelData(0)
        
        // Check if there's actual audio data (not just silence)
        const hasAudio = inputData.some(sample => Math.abs(sample) > 0.01)
        if (!hasAudio) {
          return  // Skip silent chunks
        }
        
        // Convert Float32Array to Int16Array (PCM)
        const int16Data = new Int16Array(inputData.length)
        for (let i = 0; i < inputData.length; i++) {
          // Clamp and convert to 16-bit integer
          const s = Math.max(-1, Math.min(1, inputData[i]))
          int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
        }

        // Send chunk
        if (onAudioChunk) {
          const chunkIdx = chunkIndexRef.current++
          onAudioChunk(int16Data.buffer, chunkIdx)
          if (chunkIdx % 10 === 0) {  // Log every 10th chunk to avoid spam
            console.log(`Audio chunk ${chunkIdx} captured, size: ${int16Data.buffer.byteLength} bytes`)
          }
        }
      }

      source.connect(processor)
      processor.connect(audioContext.destination)

      isCapturingRef.current = true
      setIsCapturing(true)
    } catch (err) {
      setError(err.message || 'Failed to start audio capture')
      console.error('Audio capture error:', err)
      throw err
    }
  }

  const stopRecording = () => {
    isCapturingRef.current = false
    setIsCapturing(false)

    // Stop processor
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    // Stop media stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }

    // Clear interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }

    chunkIndexRef.current = 0
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording()
    }
  }, [])

  // Handle enabled state
  useEffect(() => {
    if (!enabled && isCapturing) {
      stopRecording()
    }
  }, [enabled])

  return {
    startRecording,
    stopRecording,
    isCapturing,
    error
  }
}
