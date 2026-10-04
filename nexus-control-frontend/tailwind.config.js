export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#fff1f2',
          100: '#ffe4e6',
          200: '#fecdd3',
          300: '#fda4af',
          400: '#fb7185',
          500: '#ef1f2b',
          600: '#dc1724',
          700: '#be123c',
          800: '#9f1239',
          900: '#881337',
          950: '#24060b',
        },
        ink: {
          50: '#fafafa',
          100: '#f4f4f5',
          200: '#e4e4e7',
          300: '#d4d4d8',
          400: '#a1a1aa',
          500: '#71717a',
          600: '#52525b',
          700: '#3f3f46',
          800: '#27272a',
          900: '#18181b',
          950: '#09090b',
        },
        accent: {
          DEFAULT: 'rgb(var(--nx-accent) / <alpha-value>)',
          strong: 'rgb(var(--nx-accent-strong) / <alpha-value>)',
        },
        obsidian: {
          main: '#0C0E12',
          sidebar: '#1B0A0F',
          sidebarDeep: '#14080B',
          card: '#161920',
          cardAlt: '#1C1F2B',
          line: '#262A36',
          muted: '#8A90A0',
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          'Helvetica',
          'Arial',
          'sans-serif',
        ],
        mono: [
          '"JetBrains Mono"',
          'ui-monospace',
          'SFMono-Regular',
          'Menlo',
          'Consolas',
          'monospace',
        ],
      },
      boxShadow: {
        card: '0 1px 2px 0 rgb(15 23 42 / 0.04), 0 1px 3px 0 rgb(15 23 42 / 0.06)',
        elevated: '0 4px 16px -2px rgb(15 23 42 / 0.08), 0 2px 6px -1px rgb(15 23 42 / 0.04)',
        modal: '0 20px 50px -12px rgb(15 23 42 / 0.25)',
        glow: '0 0 24px rgb(239 31 43 / 0.35)',
      },
      borderRadius: {
        xl: '0.75rem',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
        'scale-in': {
          '0%': { opacity: 0, transform: 'scale(0.96)' },
          '100%': { opacity: 1, transform: 'scale(1)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-400px 0' },
          '100%': { backgroundPosition: '400px 0' },
        },
        'pulse-dot': {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.35 },
        },
      },
      animation: {
        'fade-in': 'fade-in 150ms ease-out',
        'scale-in': 'scale-in 150ms ease-out',
        shimmer: 'shimmer 1.4s linear infinite',
        'pulse-dot': 'pulse-dot 2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
