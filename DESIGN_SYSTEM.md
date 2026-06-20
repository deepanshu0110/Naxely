# Naxely Design System

> Single source of truth for all locked design decisions. Every prompt
> should reference this file instead of re-explaining identity.

---

## Brand Identity

| Token | Value | Usage |
|---|---|---|
| Display font | **Fraunces** (serif) | Headlines, hero numbers, brand wordmark |
| Body font | **IBM Plex Sans** | UI text, labels, paragraphs |
| Numeric/mono font | **IBM Plex Mono** | Numbers, data, timestamps |
| Primary accent | **#D97A34** (amber/terracotta) | Buttons, active states, chart accents |
| Background (light) | **#F7F2E9** (cream/paper) | Main app background |
| Secondary surface (light) | **#EAE3D3** (warm slate) | Cards, sidebars, secondary surfaces |
| Background (dark) | **#1C1A16** (warm dark) | NOT pure black, NOT cold gray/navy |
| Text (light) | **#14131F** (ink) | Default text color |
| Positive trend | **#0E9F6E** (mint) | Upward trends, semantic only |
| Negative trend | **#C13B3B** (red) | Downward trends, semantic only |

### Brand Motif

A minimal ascending-bars glyph of 3 bars increasing in height, filled
in amber (#D97A34). Used as favicon, loading animation base, and
decorative element throughout the app.

---

## Critical Rules

### Trend arrows are ALWAYS drawn vector triangles, never Unicode characters

Unicode arrows (↑ ↓ ➚ etc.) risk font-glyph-coverage across systems.
Every trend indicator MUST use a drawn SVG triangle or a styled
vector shape. This applies to: dashboard report cards, PDF report
stats, landing page hero stats, any KPI display.

### Dark mode colors are ALWAYS explicitly defined per component

Never inherit or invert from light mode values. Every component that
appears in dark mode must have explicit `dark:` Tailwind classes or
explicit CSS custom properties. The background is `dark:bg-darkBg`
(#1C1A16), not `dark:bg-black` or `dark:bg-gray-900`.

### Every primary CTA button must have an explicit background fill

In both light and dark mode. Not just a text color or border. Always:
`bg-amber-500 hover:bg-amber-600` for light, `dark:bg-amber-500
dark:hover:bg-amber-600` (or a specific dark variant).

### Brand color is user-customizable in Settings > Branding

The default brand color is amber (#D97A34), but Pro/Agency users can
override it for white-label PDF generation. This override is
intentional and MUST NOT be touched when "fixing" color issues. The
override only affects PDF cover pages and chart styling, not the web
app chrome.

---

## Color Tokens

These are defined in `frontend/src/design-tokens.ts` and mapped in
`frontend/tailwind.config.ts`.

```typescript
// design-tokens.ts — canonical source
COLORS = {
  ink:        '#14131F',     // text
  paper:      '#F7F2E9',     // bg light
  slate: {                   // secondary surface, full ramp
    DEFAULT:  '#EAE3D3',
    50-950:   (generated from #EAE3D3)
  },
  cream:      '#F7F2E9',     // alias for paper
  warmSlate:  '#EAE3D3',     // alias for slate
  indigo: {                  // reserved, full ramp
    DEFAULT:  '#6366F1',
    50-950:   (generated from #6366F1)
  },
  amber: {                   // primary accent, full ramp
    DEFAULT:  '#D97A34',
    50-950:   (generated from #D97A34)
  },
  mint:       '#0E9F6E',     // positive trend
  darkBg:     '#1C1A16',     // dark mode background
}
```

---

## Files Using These Tokens

*(This list is updated as each phase touches new files.)*

### Phase 1 — Brand motif + favicon

| File | What it does |
|---|---|
| `frontend/public/favicon.svg` | SVG brand motif glyph (3 ascending bars) |
| `frontend/index.html` | Favicon link, apple-touch-icon |
| `DESIGN_SYSTEM.md` | This file |
