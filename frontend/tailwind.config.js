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
        canvas: 'rgb(var(--color-canvas) / <alpha-value>)',
        surface: 'rgb(var(--color-surface) / <alpha-value>)',
        border: 'rgb(var(--color-border) / <alpha-value>)',
        ink: 'rgb(var(--color-ink) / <alpha-value>)',
        charcoal: 'rgb(var(--color-charcoal) / <alpha-value>)',
        muted: 'rgb(var(--color-muted) / <alpha-value>)',
        accent: 'rgb(var(--color-accent) / <alpha-value>)',
        pale: {
          red: 'rgb(var(--color-pale-red) / <alpha-value>)',
          blue: 'rgb(var(--color-pale-blue) / <alpha-value>)',
          green: 'rgb(var(--color-pale-green) / <alpha-value>)',
          yellow: 'rgb(var(--color-pale-yellow) / <alpha-value>)',
        },
        paleText: {
          red: 'rgb(var(--color-paleText-red) / <alpha-value>)',
          blue: 'rgb(var(--color-paleText-blue) / <alpha-value>)',
          green: 'rgb(var(--color-paleText-green) / <alpha-value>)',
          yellow: 'rgb(var(--color-paleText-yellow) / <alpha-value>)',
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
