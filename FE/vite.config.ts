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
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
      manifest: {
        name: 'AiTime',
        short_name: 'AiTime',
        description: 'AiTime - 우리 아이 자폐 조기 선별',
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
          proxy.on('proxyRes', (proxyRes, req, res) => {
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