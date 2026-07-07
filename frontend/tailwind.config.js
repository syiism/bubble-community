/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['SF Pro Display', 'Geist Sans', 'Helvetica Neue', 'Switzer', 'sans-serif'],
        serif: ['Lyon Text', 'Newsreader', 'Playfair Display', 'Instrument Serif', 'serif'],
        mono: ['Geist Mono', 'SF Mono', 'JetBrains Mono', 'monospace'],
      },
      colors: {
        canvas: '#F7F6F3',
        surface: '#FFFFFF',
        border: '#EAEAEA',
        ink: '#111111',
        charcoal: '#2F3437',
        muted: '#787774',
        accent: '#b8693d',
        pale: {
          red: '#FDEBEC',
          blue: '#E1F3FE',
          green: '#EDF3EC',
          yellow: '#FBF3DB',
        },
        paleText: {
          red: '#9F2F2D',
          blue: '#1F6C9F',
          green: '#346538',
          yellow: '#956400',
        }
      },
      boxShadow: {
        subtle: '0 2px 8px rgba(0,0,0,0.04)',
        hover: '0 4px 12px rgba(0,0,0,0.05)',
      },
      animation: {
        'fade-up': 'fadeUp 600ms cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'stagger': 'fadeUp 600ms cubic-bezier(0.16, 1, 0.3, 1) forwards',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      }
    },
  },
  plugins: [],
}
