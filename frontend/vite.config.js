/**
 * Vite Configuration
 * ==================
 * Vite is the build tool and development server for our React app.
 *
 * LEARNING — The Proxy:
 *   During development, our React app runs on port 5173 and Django runs on 8000.
 *   Without a proxy, every API call from the browser would be:
 *     fetch('http://localhost:8000/api/transactions/')
 *   With the proxy configured below, we can write:
 *     fetch('/api/transactions/')
 *   Vite intercepts any request starting with /api and forwards it to port 8000.
 *
 *   This also avoids CORS issues in development because from the BROWSER's
 *   perspective, the request goes to the same origin (port 5173).
 */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
