export const COLORS = {
  ink: '#14131F' as const,
  paper: '#FAFAFC' as const,
  slate: '#F3F2F8' as const,
  indigo: '#6366F1' as const,
  amber: '#D97A34' as const,
  mint: '#0E9F6E' as const,
} as const

export type ColorKey = keyof typeof COLORS

export const FONTS = {
  display: ['Space Grotesk', 'sans-serif'] as string[],
  body: ['IBM Plex Sans', 'sans-serif'] as string[],
  mono: ['IBM Plex Mono', 'monospace'] as string[],
} as const

export type FontKey = keyof typeof FONTS
