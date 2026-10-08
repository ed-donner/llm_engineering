import { useState, useEffect } from 'react'
import axios from 'axios'

interface ApiResponse {
  message: string
}

export function useHello() {
  const [message, setMessage] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    axios.get<ApiResponse>('/api/hello')
      .then((response) => {
        setMessage(response.data.message)
        setError(null)
        setLoading(false)
      })
      .catch((err: unknown) => {
        console.error('Error fetching hello:', err)
        setMessage('Error connecting to backend')
        setError('Error connecting to backend')
        setLoading(false)
      })
  }, [])

  return { message, loading, error }
}

