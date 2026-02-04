import { defineConfig } from 'vite'
import path from 'path'
import { fileURLToPath } from 'url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

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
  // 1. 개발 서버 설정 (npm run dev)
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
  // 2. 프리뷰 서버 설정 (npm run preview) - 이 부분을 추가하세요!
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