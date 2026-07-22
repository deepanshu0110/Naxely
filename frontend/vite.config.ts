import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { FontaineTransform } from 'fontaine'
import path from 'path'

export default defineConfig({
  plugins: [
    FontaineTransform.vite({}),
    react(),
    {
      name: 'client-chunks',
      config(config) {
        if (!config.build?.ssr) {
          config.build = config.build || {}
          config.build.rollupOptions = config.build.rollupOptions || {}
          config.build.rollupOptions.output = {
            manualChunks: {
              vendor: ['react', 'react-dom', 'react-router-dom'],
              charts: ['recharts'],
              supabase: ['@supabase/supabase-js'],
            },
          }
        }
      },
    },
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
  ssgOptions: {
    mock: true,
    dirStyle: 'nested',
    includedRoutes() {
      return ['/', '/pricing', '/contact', '/terms', '/privacy', '/refund', '/blog', '/blog/byok-ai-reporting-tool', '/blog/csv-to-pdf-report-generator', '/blog/white-label-client-reporting-agencies', '/blog/automating-client-reports', '/blog/client-reporting-software-guide', '/blog/best-client-reporting-software-freelancers', '/blog/python-csv-to-pdf-reports', '/blog/two-weeks-building-naxely', '/blog/what-should-client-report-include-checklist', '/blog/client-reporting-for-freelance-consultants', '/blog/client-reporting-tools-for-upwork-freelancer', '/blog/client-reporting-tools-flat-pricing', '/compare/agencyanalytics', '/compare/databox', '/compare/powerdrill', '/compare/dashthis', '/compare/whatagraph', '/faq', '/changelog']
    },
  },
})
