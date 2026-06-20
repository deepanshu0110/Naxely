export const COLORS = {
  ink: '#14131F' as const,
  paper: '#F7F2E9' as const,
  slate: {
    DEFAULT: '#EAE3D3' as const,
    50: '#FEFEFD' as const,
    100: '#FCFBF8' as const,
    200: '#F7F4ED' as const,
    300: '#F1EDE2' as const,
    400: '#EDE7DA' as const,
    500: '#EAE3D3' as const,
    600: '#BBB6A9' as const,
    700: '#989489' as const,
    800: '#75726A' as const,
    900: '#524F4A' as const,
    950: '#2F2D2A' as const,
  } as const,
  cream: '#F7F2E9' as const,
  warmSlate: '#EAE3D3' as const,
  indigo: {
    DEFAULT: '#6366F1' as const,
    50: '#F7F7FE' as const,
    100: '#E8E8FD' as const,
    200: '#C1C2F9' as const,
    300: '#9A9CF6' as const,
    400: '#7A7DF3' as const,
    500: '#6366F1' as const,
    600: '#4F52C1' as const,
    700: '#40429D' as const,
    800: '#323379' as const,
    900: '#232454' as const,
    950: '#141430' as const,
  } as const,
  amber: {
    50: '#FDF8F5',
    100: '#FAEFE7',
    200: '#F4D7C2',
    300: '#EDBF9E',
    400: '#E5A575',
    500: '#D97A34',
    600: '#A95F29',
    700: '#82491F',
    800: '#5B3316',
    900: '#38200E',
    950: '#1E1107',
  } as const,
  mint: '#0E9F6E' as const,
  darkBg: '#1C1A16' as const,
} as const

export type ColorKey = keyof typeof COLORS

export const FONTS = {
  display: ['Fraunces', 'Georgia', 'serif'] as string[],
  body: ['IBM Plex Sans', 'system-ui', 'sans-serif'] as string[],
  mono: ['IBM Plex Mono', 'monospace'] as string[],
} as const

export type FontKey = keyof typeof FONTS
