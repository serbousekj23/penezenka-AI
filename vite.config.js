import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// URL frontend služby na Renderu
const FRONTEND_HOST = 'penezenka-ai-frontend.onrender.com'

export default defineConfig({
  plugins: [svelte()],
  preview: {
    host: '0.0.0.0',                   // aby Render mohl detekovat port
    port: process.env.PORT || 4173,    // dynamický port z Renderu
    allowedHosts: [FRONTEND_HOST]      // povolit host pro Render URL
  },
  define: {
    // URL backendu, fallback na localhost pro lokální testy
    'process.env.VITE_API_BASE': JSON.stringify(
      process.env.VITE_API_BASE || 'http://localhost:5000'
    )
  }
})