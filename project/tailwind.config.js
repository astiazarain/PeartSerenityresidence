/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        gold: {
          50:  '#fdf8ed',
          100: '#faefc9',
          200: '#f5db89',
          300: '#f0c442',
          400: '#e7ae25',
          500: '#c8920a',
          600: '#a67508',
          700: '#865c07',
          800: '#6b4a0a',
          900: '#573d0d',
          950: '#302007',
        },
        brand: {
          black:   '#0D0D0D',
          charcoal:'#26201A',
          cream:   '#FBF6E9',
          softgrey:'#EFEADC',
          textgrey:'#666666',
        },
      },
      fontFamily: {
        serif: ['Playfair Display', 'serif'],
        sans:  ['Inter', 'sans-serif'],
      },
      animation: {
        'fade-in':  'fadeIn 0.8s ease-out forwards',
        'slide-up': 'slideUp 0.6s ease-out forwards',
      },
    },
  },
  plugins: [],
};
