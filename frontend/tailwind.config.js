/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
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
        canvas: 'var(--color-canvas)',
        surface: 'var(--color-surface)',
        border: 'var(--color-border)',
        ink: 'var(--color-ink)',
        charcoal: 'var(--color-charcoal)',
        muted: 'var(--color-muted)',
        accent: 'var(--color-accent)',
        pale: {
          red: 'var(--color-pale-red)',
          blue: 'var(--color-pale-blue)',
          green: 'var(--color-pale-green)',
          yellow: 'var(--color-pale-yellow)',
        },
        paleText: {
          red: 'var(--color-paleText-red)',
          blue: 'var(--color-paleText-blue)',
          green: 'var(--color-paleText-green)',
          yellow: 'var(--color-paleText-yellow)',
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
