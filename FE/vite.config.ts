import { defineConfig } from 'vite'
import path from 'path'
import { fileURLToPath } from 'url' // 1. 이 줄 추가
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

// 2. __dirname을 요즘 방식(ESM)으로 직접 만들어주는 코드
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      devOptions: {
        enabled: true
      },
      manifest: {
        name: 'AiTime',
        short_name: 'AiTime',
        theme_color: '#ffffff',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
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
  server: {
    proxy: {
      '/api': {
        target: 'http://70.12.246.92:8080',
        changeOrigin: true,
        secure: false,
        cookieDomainRewrite: {
          "*": ""
        },
        cookiePathRewrite: {
          "*": "/"
        },
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            proxyReq.setHeader('Origin', 'http://70.12.246.92:8080');
          });
        },
      },
    },
  },
})
