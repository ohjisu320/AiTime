/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // [부모용] 소프트 라벤더
        lavender: {
          DEFAULT: '#E6E6FA',
          dark: '#D8BFD8',
          light: '#F3E5F5'
        },
        // [의료진용] 메디컬 블루
        medical: {
          DEFAULT: '#4F46E5', // Indigo-600
          dark: '#3730A3',    // Indigo-800
          light: '#818CF8'    // Indigo-400
        }
      },
      fontFamily: {
        sans: ['Pretendard', 'sans-serif'],
      }
    },
  },
  plugins: [],
}