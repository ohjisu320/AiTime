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
})