/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        azul: {
          50: '#EBF0FA',
          100: '#C7D6F0',
          200: '#9FB8E5',
          300: '#6F96D9',
          400: '#4A78D0',
          500: '#1A56C4',
          600: '#0047B3',
          700: '#003399',
          800: '#002680',
          900: '#001A66',
        },
      },
    },
  },
  plugins: [],
};
