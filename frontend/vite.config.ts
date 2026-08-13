import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    port: 5173,
  },
  build: {
    rollupOptions: {
      output: {
        // Keeps the public-bundle screens (institutional block, etc.) in
        // their own chunk, separate from the authenticated app -- PARTE 5
        // requires the authenticated bundle to not be fetched before the
        // access check resolves to AUTHORIZED. Route-level lazy imports
        // (see src/app/router.tsx) are what actually defer the fetch; this
        // just keeps the chunk boundaries clean so that's verifiable in
        // the network tab / build output.
        manualChunks(id) {
          if (id.includes('src/public-bundle')) return 'public-bundle'
        },
      },
    },
  },
})
