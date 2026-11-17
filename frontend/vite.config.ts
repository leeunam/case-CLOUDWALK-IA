import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': 'http://api:3000',
      '/webhooks': 'http://api:3000',
      '/cable': { target: 'ws://api:3000', ws: true },
    },
  },
})
