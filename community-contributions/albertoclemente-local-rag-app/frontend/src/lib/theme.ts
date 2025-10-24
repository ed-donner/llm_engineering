'use client'

import { useEffect, useState } from 'react'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'ui.theme'

export function getStoredTheme(): Theme | null {
  if (typeof window === 'undefined') return null
  const v = window.localStorage.getItem(STORAGE_KEY)
  return v === 'light' || v === 'dark' ? v : null
}

export function setStoredTheme(theme: Theme) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(STORAGE_KEY, theme)
}

export function getSystemTheme(): Theme {
  if (typeof window === 'undefined') return 'light'
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
  return prefersDark ? 'dark' : 'light'
}

export function applyTheme(theme: Theme) {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  root.classList.remove('theme-light', 'theme-dark')
  root.classList.add(theme === 'dark' ? 'theme-dark' : 'theme-light')
}

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(() => getStoredTheme() || getSystemTheme())

  useEffect(() => {
    applyTheme(theme)
    setStoredTheme(theme)
  }, [theme])

  const setTheme = (t: Theme) => setThemeState(t)

  return { theme, setTheme }
}
