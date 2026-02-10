import { defineConfig } from 'vite'
import path from 'path'
import { fileURLToPath } from 'url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
      },
      includeAssets: ['favicon.ico', 'favicon.svg', 'apple-touch-icon.png'],
      manifest: {
        name: '아이타임(AiTime)',
        short_name: 'AiTime',
        description: 'AiTime - 우리 아이 자폐 조기 선별 서비스',
        theme_color: '#6366F1',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'any',
        start_url: '/',
        scope: '/',
        icons: [
          {
            src: 'web-app-manifest-192x192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any'
          },
          {
            src: 'web-app-manifest-192x192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'maskable'
          },
          {
            src: 'web-app-manifest-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any'
          },
          {
            src: 'web-app-manifest-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable'
          },
          {
            src: 'apple-touch-icon.png',
            sizes: '180x180',
            type: 'image/png',
            purpose: 'any'
          }
        ]
      },
      devOptions: {
        enabled: true
      }
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        api: 'modern-compiler',
        silenceDeprecations: ['import'],
      },
    },
  },
  build: {
    target: 'es2020',
    minify: 'esbuild',
    rollupOptions: {
      output: {
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
        // Vite 자동 청크 분할에 맡김 (manualChunks 제거)
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  server: {
    proxy: {
      '/api/v1': {
        target: 'http://70.12.246.95:8080',
        changeOrigin: true,
        secure: false,
        cookieDomainRewrite: {
          "*": ""
        },
        cookiePathRewrite: {
          "*": "/"
        },
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, _req, _res) => {
            proxyReq.setHeader('Origin', 'http://70.12.246.95:8080');
          });
          proxy.on('proxyRes', (proxyRes, _req, _res) => {
            const cookies = proxyRes.headers['set-cookie'];
            if (cookies) {
              proxyRes.headers['set-cookie'] = cookies.map(cookie =>
                cookie.replace(/SameSite=Strict/gi, 'SameSite=Lax')
              );
            }
          });
        },
      },
    },
  },
  preview: {
    proxy: {
      '/api': {
        target: 'https://i14a501.p.ssafy.io',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})