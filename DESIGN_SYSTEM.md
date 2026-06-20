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
| Negative trend | **#EF4444** (red) | Downward trends, semantic only |

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

### Frontend (`frontend/src/design-tokens.ts`)

Mapped in `frontend/tailwind.config.ts`.

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

### Backend (`backend/app/core/design_tokens.py`)

Used by `pdf_service.py` and `chart_service.py` for PDF/chart generation.

```python
# design_tokens.py — canonical source for backend rendering
INK = "#14131F"
PAPER = "#F7F2E9"
SLATE = "#EAE3D3"
CREAM = "#F7F2E9"
WARM_SLATE = "#EAE3D3"
INDIGO = "#6366F1"
AMBER = "#D97A34"
MINT = "#0E9F6E"         # positive trend
RED = "#EF4444"           # negative trend
BRAND_COLOR = AMBER       # default, overridable in Settings > Branding
FONT_DISPLAY = "'Fraunces', Georgia, serif"
FONT_BODY = "'IBM Plex Sans', system-ui, sans-serif"
FONT_MONO = "'IBM Plex Mono', monospace"
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

### Phase 2 — Tactile paper texture (web app only)

| File | What it does |
|---|---|
| `frontend/public/noise-texture.svg` | SVG feTurbulence fractal noise (300×300, grayscale) |
| `frontend/src/index.css` | `#root::before` overlay w/ `mix-blend-mode: multiply`, 4% opacity light / 1.2% dark |
| `DESIGN_SYSTEM.md` | This file |

> PDF note: ReportLab can't render SVG feTurbulence filters natively.
> Embedding a rasterized noise PNG would add ~5-10 KB per PDF. Skipped
> for now — the texture is strong enough in the web app alone to establish
> the tactile identity. Revisit if the brand calls for it.

### Phase 3 — Report generation loading animation

| File | What it does |
|---|---|
| `frontend/src/components/report/GeneratingLoader.tsx` | 6-bar growing animation above checklist; replaces `Loader2` spinner + progress bar |
| `DESIGN_SYSTEM.md` | This file |

### Phase 4 — Count-up animation hook

| File | What it does |
|---|---|
| `frontend/src/hooks/useCountUp.ts` | `useCountUp` — rAF-based number animation with easeOutQuad, `useReducedMotion` guard, format-preserving parse/reapply |
| `frontend/src/hooks/__tests__/useCountUp.test.ts` | 10 vitest tests covering parse + reapply edge cases |
| `DESIGN_SYSTEM.md` | This file |

### Phase 5 — Empty state illustration

| File | What it does |
|---|---|
| `frontend/src/pages/Dashboard.tsx` | Inline SVG — document outline + chart bars + magnifying glass, amber strokes |
| `frontend/src/components/ui/EmptyState.tsx` | Title changed to `font-display` (Fraunces) for consistent heading hierarchy |
| `DESIGN_SYSTEM.md` | This file |

---

## Illustration Style

Phase 5 introduced the first **stroke-based SVG illustration** in the app. All prior
SVG assets (favicon, loading bars) use filled shapes. This illustration debuts the
outline-only style for empty/decorative states.

| Attribute | Value | Notes |
|---|---|---|
| Stroke color | `#D97A34` (amber, `--color-amber-500`) | Matches primary accent |
| Stroke width | `1.5` on `120×120` viewBox (~1.25% of viewBox) | Deliberately thinner than the old `2` used in the pre-Phase-5 inline SVG; refined for pure-outline look |
| Line caps/joins | `round` | Softens the stroke ends |
| Fill | `none` | All elements are outlines |
| ViewBox | `120×120` | Scales cleanly at 64px, 120px, 200px — tested in all three |
| Composition | Document outline (rounded rect) + 3 header lines + 3 ascending bar-chart bars + magnifying-glass circle+handle accent overlapping top-right | |

This style is intended to be reusable for other empty states (no API key, no branding,
etc.) — each would get its own distinct icon in the same stroke-only amber treatment.

### Phase 6 — PDF cover page redesign

| File | What it does |
|---|---|
| `backend/app/services/pdf_service.py` | `_CoverMotif` — brand motif flowable (48×48pt, 3 ascending bars, common baseline, brand color); `_CoverRule` — 0.5pt horizontal rule (GRID_LINE); both wired into `build_sync()` |
| `backend/app/core/design_tokens.py` | Added `GRID_LINE = "#D1D5DB"` token; two hardcoded `#D1D5DB` in data table grids replaced with import |
| `DESIGN_SYSTEM.md` | This file |

### Phase 7 — Landing page hero redesign

| File | What it does |
|---|---|
| `frontend/src/pages/Landing.tsx` | Hero: mini Phase 6 PDF cover (amber band, 3 ascending bars, thin rule, revenue stat + mint trend arrow, mini chart bars); chrome/document split (chrome gets `dark:` treatment, mini-cover invariant); CTA uses `<Button variant="primary">`; dot-pattern background via `--dot-color` CSS variable |
| `DESIGN_SYSTEM.md` | This file |

### Phase 8 — Bento features grid

| File | What it does |
|---|---|
| `frontend/src/pages/Landing.tsx` | Asymmetric 3×3 CSS grid: AI Executive Summary at col-span-2 row-span-2, 5 smaller cards in remaining cells; lucide-react icons rendered as amber line-icons; Google Sheets gets "Coming Soon" badge; dark-mode separation via `dark:border-amber-900/50` |
| `DESIGN_SYSTEM.md` | This file |

### Phase 9 — Dashboard reports list rows

| File | What it does |
|---|---|
| `frontend/src/components/dashboard/ReportCard.tsx` | Card grid → single-column rows: FileText icon thumbnail, title + date (truncated), row count (useCountUp), status badge (semantic Badge colors), always-visible download icon, 3-dot menu (View + Delete) |
| `frontend/src/pages/Dashboard.tsx` | Grid layout changed from `grid grid-cols-1 gap-4 md:grid-cols-2` to `space-y-3` single-column rows; empty state (Phase 5) untouched |
| `DESIGN_SYSTEM.md` | This file |
