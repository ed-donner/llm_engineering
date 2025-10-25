'use client'

import { useEffect, useState } from 'react'
import { Wifi, WifiOff, Cpu, HardDrive, Activity, Clock } from 'lucide-react'
import { useSystemStatus } from '@/hooks/api'
import { cn } from '@/lib/utils'

export function StatusBar() {
  const { data: status, isError } = useSystemStatus()
  const [currentTime, setCurrentTime] = useState<string>('')

  useEffect(() => {
    // Update time immediately and then every second
    const updateTime = () => {
      setCurrentTime(new Date().toLocaleTimeString())
    }
    
    updateTime()
    const interval = setInterval(updateTime, 1000)
    
    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = () => {
    if (isError || !status) return <WifiOff className="h-4 w-4 text-red-500" />
    
    switch (status.status) {
      case 'operational':
        return <Wifi className="h-4 w-4 text-green-500" />
      case 'degraded':
        return <Activity className="h-4 w-4 text-yellow-500" />
      case 'offline':
      case 'error':
        return <WifiOff className="h-4 w-4 text-red-500" />
      default:
        return <Wifi className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusText = () => {
    if (isError) return 'Connection Error'
    if (!status) return 'Connecting...'
    
    switch (status.status) {
      case 'operational':
        return 'Online'
      case 'degraded':
        return 'Degraded'
      case 'offline':
        return 'Offline'
      case 'error':
        return 'Error'
      default:
        return 'Unknown'
    }
  }

  const formatPercentage = (value: number | null | undefined) => {
    return value == null ? 'N/A' : `${Math.round(value)}%`
  }

  const formatMemoryUsage = (value: number | null | undefined) => {
    if (value == null) return 'N/A'
    return `${(value / 1024 / 1024 / 1024).toFixed(1)}GB`
  }

  return (
    <div className="h-8 bg-gray-800 text-white px-4 flex items-center justify-between text-xs">
      {/* Left Side - Connection Status */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-1">
          {getStatusIcon()}
          <span>{getStatusText()}</span>
        </div>
        
        {status?.offline && (
          <div className="flex items-center space-x-1 text-yellow-400">
            <WifiOff className="h-3 w-3" />
            <span>Local Mode</span>
          </div>
        )}
      </div>

      {/* Center - System Resources */}
      <div className="flex items-center space-x-6">
        {/* CPU Usage */}
        <div className="flex items-center space-x-1">
          <Cpu className="h-3 w-3 text-blue-400" />
          <span className="text-gray-300">CPU:</span>
          <span className={cn(
            'font-mono',
            status?.cpu_usage != null && status.cpu_usage > 80 ? 'text-red-400' :
            status?.cpu_usage != null && status.cpu_usage > 60 ? 'text-yellow-400' : 'text-green-400'
          )}>
            {formatPercentage(status?.cpu_usage)}
          </span>
        </div>

        {/* RAM Usage */}
        <div className="flex items-center space-x-1">
          <HardDrive className="h-3 w-3 text-purple-400" />
          <span className="text-gray-300">RAM:</span>
          <span className="text-white font-mono">
            {formatMemoryUsage(status?.ram_usage)}
          </span>
        </div>

        {/* Indexing Progress */}
        {status?.indexing_progress !== undefined && status.indexing_progress < 100 && (
          <div className="flex items-center space-x-1">
            <Clock className="h-3 w-3 text-orange-400 animate-spin" />
            <span className="text-gray-300">Indexing:</span>
            <span className="text-orange-400 font-mono">
              {formatPercentage(status.indexing_progress)}
            </span>
          </div>
        )}
      </div>

      {/* Right Side - Additional Info */}
      <div className="flex items-center space-x-4">
        <div className="text-gray-400">
          Local RAG WebApp v1.0
        </div>
        
        {currentTime && (
          <div className="text-gray-400" suppressHydrationWarning>
            {currentTime}
          </div>
        )}
      </div>
    </div>
  )
}
