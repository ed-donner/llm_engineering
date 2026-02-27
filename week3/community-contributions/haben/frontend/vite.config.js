import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0', // Allow external connections for Docker
    proxy: {
      '/ws': {
        target: process.env.VITE_API_URL || 'ws://localhost:8000',
        ws: true,
        changeOrigin: true
      },
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  preview: {
    port: 80,
    host: '0.0.0.0'
  }
})
