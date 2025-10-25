'use client'

import React, { createContext, useContext, useMemo, useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { Theme, useTheme } from '@/lib/theme'

interface AppProvidersProps {
  children: React.ReactNode
}

type ThemeContextType = {
  theme: Theme
  setTheme: (t: Theme) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function useThemeContext() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useThemeContext must be used within AppProviders')
  return ctx
}

export function AppProviders({ children }: AppProvidersProps) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 2,
          },
          mutations: {
            retry: 1,
          },
        },
      })
  )

  const { theme, setTheme } = useTheme()

  const toastOptions = useMemo(
    () => ({
      style: { background: 'var(--bg-elev)', color: 'var(--text-primary)' },
      duration: 4000,
      success: { iconTheme: { primary: '#10B981', secondary: '#D1FAE5' } },
      error: { iconTheme: { primary: '#EF4444', secondary: '#FEE2E2' } },
    }),
    []
  )

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeContext.Provider value={{ theme, setTheme }}>
        <Toaster toastOptions={toastOptions as any} position="top-right" />
        {children}
      </ThemeContext.Provider>
    </QueryClientProvider>
  )
}
