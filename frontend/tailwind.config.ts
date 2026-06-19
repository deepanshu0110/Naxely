import type { Config } from 'tailwindcss'
import { COLORS, FONTS } from './src/design-tokens'

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
        accent: {
          DEFAULT: '#D97A34',
          hover: '#C06A2E',
          light: '#FDF1E6',
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
        ink: COLORS.ink,
        paper: COLORS.paper,
        slate: COLORS.slate,
        cream: COLORS.cream,
        warmSlate: COLORS.warmSlate,
        amber: COLORS.amber,
        mint: COLORS.mint,
        darkBg: COLORS.darkBg,
      },
      fontFamily: {
        sans: FONTS.body,
        display: FONTS.display,
        body: FONTS.body,
        mono: FONTS.mono,
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