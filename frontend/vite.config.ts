import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/repositories': 'http://localhost:8000',
      '/investigations': 'http://localhost:8000',
    }
  }
})
