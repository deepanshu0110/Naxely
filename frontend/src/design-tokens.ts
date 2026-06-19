export const COLORS = {
  ink: '#14131F' as const,
  paper: '#F7F2E9' as const,
  slate: '#EAE3D3' as const,
  cream: '#F7F2E9' as const,
  warmSlate: '#EAE3D3' as const,
  indigo: '#6366F1' as const,
  amber: '#D97A34' as const,
  mint: '#0E9F6E' as const,
} as const

export type ColorKey = keyof typeof COLORS

export const FONTS = {
  display: ['Fraunces', 'Georgia', 'serif'] as string[],
  body: ['IBM Plex Sans', 'system-ui', 'sans-serif'] as string[],
  mono: ['IBM Plex Mono', 'monospace'] as string[],
} as const

export type FontKey = keyof typeof FONTS
