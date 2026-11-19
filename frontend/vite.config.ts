import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const target = loadEnv(mode, '.', 'API_PROXY_').API_PROXY_TARGET || 'http://api:3000'
  return {
    plugins: [react()],
    server: {
      port: 5173,
      strictPort: true,
      proxy: {
        '/api': target,
        '/webhooks': target,
        '/cable': { target, ws: true },
      },
    },
  }
})
