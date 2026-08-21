import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/documents': 'http://localhost:8000',
      '/story': 'http://localhost:8000',
      '/themes': 'http://localhost:8000',
      '/topics': 'http://localhost:8000',
      '/subplots': 'http://localhost:8000',
      '/encoding-rules': 'http://localhost:8000',
      '/sidekick': 'http://localhost:8000',
      '/ingest': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
