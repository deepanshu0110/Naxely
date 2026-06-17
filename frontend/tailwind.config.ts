import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Match FSD design system exactly
        accent: {
          DEFAULT: '#6366F1',
          hover: '#4F46E5',
          light: '#EEF2FF',
        },
        brand: {
          bg: '#FFFFFF',
          subtle: '#F9FAFB',
          muted: '#F3F4F6',
          border: '#E5E7EB',
        },
        chart: {
          1: '#6366F1',
          2: '#10B981',
          3: '#F59E0B',
          4: '#EF4444',
          5: '#3B82F6',
          6: '#8B5CF6',
          7: '#EC4899',
          8: '#14B8A6',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      borderRadius: {
        lg: '0.5rem',
        md: '0.375rem',
        sm: '0.25rem',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}

export default config