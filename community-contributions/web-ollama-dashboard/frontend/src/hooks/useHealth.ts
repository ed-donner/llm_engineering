import { useState, useEffect } from 'react'
import axios from 'axios'

interface HealthResponse {
  status: string
  message?: string
}

export function useHealth() {
  const [healthStatus, setHealthStatus] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    axios.get<HealthResponse>('/api/health')
      .then((response) => {
        setHealthStatus(response.data.status)
        setError(null)
        setLoading(false)
      })
      .catch((err: unknown) => {
        console.error('Error fetching health:', err)
        setHealthStatus('offline')
        setError('Error connecting to backend')
        setLoading(false)
      })
  }, [])

  return { healthStatus, loading, error }
}

