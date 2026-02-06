import { defineConfig } from 'vite'
import path from 'path'
import { fileURLToPath } from 'url' // 1. 이 줄 추가
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

// 2. __dirname을 요즘 방식(ESM)으로 직접 만들어주는 코드
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        api: 'modern-compiler', // 최신 Sass 컴파일러 사용
        silenceDeprecations: ['import'], // @import 관련 경고 숨기기
      },
    },
  },
  // 1. 개발 서버 설정 (npm run dev)
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
  // 2. 프리뷰 서버 설정 (npm run preview)
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
