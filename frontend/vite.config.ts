import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const target = loadEnv(mode, '.', 'API_PROXY_').API_PROXY_TARGET || 'http://api:3000'
  // Rails compara a origem do navegador com o Host recebido ao validar CSRF.
  const proxy = { target, changeOrigin: false }
  return {
    plugins: [react()],
    server: {
      port: 5173,
      strictPort: true,
      proxy: {
        '/api': proxy,
        '/webhooks': proxy,
        '/cable': { ...proxy, ws: true },
      },
    },
  }
})
