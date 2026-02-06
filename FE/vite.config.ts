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
      includeAssets: ['favicon.ico', 'favicon.svg', 'apple-touch-icon.png'],
      manifest: {
        name: '아이타임(AiTime)',
        short_name: 'AiTime',
        description: 'AiTime - 우리 아이 자폐 조기 선별 서비스',
        theme_color: '#6366F1',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait',
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
    rollupOptions: {
      output: {
        // 청크 파일명에 해시를 포함하여 캐시 문제 방지
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
        // 청크 분할 전략 최적화
        manualChunks: (id) => {
          // node_modules는 vendor 청크로 분리
          if (id.includes('node_modules')) {
            // 큰 라이브러리들은 별도 청크로 분리
            if (id.includes('livekit')) return 'livekit-vendor';
            if (id.includes('react-router')) return 'router-vendor';
            if (id.includes('react') || id.includes('react-dom')) return 'react-vendor';
            return 'vendor';
          }
          // 페이지별 청크 분할
          if (id.includes('/features/exam/')) return 'exam-feature';
          if (id.includes('/features/monitoring/')) return 'monitoring-feature';
        },
      },
    },
    // 청크 크기 경고 임계값 조정
    chunkSizeWarningLimit: 1000,
  },
  // 1. 개발 서버 설정 (npm run dev)
  server: {
    proxy: {
      '/api/v1': {
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
          proxy.on('proxyReq', (proxyReq, _req, _res) => {
            proxyReq.setHeader('Origin', 'http://70.12.246.92:8080');
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