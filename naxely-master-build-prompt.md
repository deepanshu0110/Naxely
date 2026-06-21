# Naxely — Master Design & Bug-Fix Prompt

You are executing a full design pass on Naxely, combining regression
fixes with new visual identity work. Work through phases STRICTLY IN
ORDER. After EACH phase: run the test suite, commit, and push so it
deploys to Render/Vercel, then STOP and tell me it's deployed and
ready to check live — do not take screenshots yourself, do not
proceed to the next phase until I confirm I've checked the live app
and approved. This project has had repeated regressions slip through
from incomplete verification — do not skip these checkpoints.

IMPORTANT: "Tests passing" is not sufficient sign-off for a visual
phase. Several issues in this project (missing PDF arrows, dark mode
contrast, unfilled buttons) shipped with passing tests. Every phase
needs a real deploy + my live check before the next phase starts.

## Locked identity reference
- Display font: **Fraunces** (serif) — headlines, hero numbers, brand wordmark
- Body font: **IBM Plex Sans** — UI text, labels, paragraphs
- Numeric font: **IBM Plex Mono** — numbers, data, timestamps
- Primary accent: **#D97A34** (amber/terracotta) — buttons, active states, chart accents
- Background (light): **#F7F2E9** (cream)
- Secondary surface (light): warm slate, ~#EAE3D3
- Background (dark): warm dark tone ~#1C1A16 — NOT pure black, NOT cold gray/navy
- Trend colors: mint (#0E9F6E) positive, red (#C13B3B) negative — semantic only, not brand colors
- User-customizable brand color (Settings > Branding) overrides amber in PDFs for white-labeling — this is intentional, never touch that logic when fixing "color" issues

---

## PHASE 0A — Fix: missing PDF trend arrows

BEFORE CHANGING ANYTHING, show me the exact code rendering the trend
arrow (↑/↓) on the cover page hero stat and KPI Metrics Overview cards
— specifically what font is applied to that text run.

CONTEXT: The coral/red sometimes seen in test PDFs is the user's own
custom Branding > Brand Colour override — correct behavior, don't touch.

FIX: Arrows have disappeared, likely because this text run switched to
Fraunces, which probably lacks these Unicode glyphs, so ReportLab
silently drops them. Fix by replacing the Unicode arrow with a small
**drawn vector triangle** (ReportLab can draw simple paths/polygons
directly) — not font-dependent, can't silently break again. Color the
triangle red (pointing down) or mint (pointing up) based on sign.

VERIFY: Regenerate a report with DEFAULT brand color, export cover
page + KPI overview as PNG, confirm arrows visible and correctly
oriented.

---

## PHASE 0B — Fix: dark mode contrast + button fill regressions

Before changing anything, show me current code for:
1. Sidebar nav item component (active + inactive, light + dark classes)
2. Settings page tab component (active + inactive, light + dark)
3. Dark mode toggle switch (full markup, track/thumb color logic both states)
4. "Next"/primary button in the Map Columns wizard — confirm if it has
   any background-color class or only text-color

FIX A — Sidebar nav + Settings tabs, dark mode contrast: define
EXPLICIT dark-mode tokens, not inherited/inverted from light mode.
Inactive text: readable light gray (70-80% lightness), not pure white.
Active text/indicator: NOT the same `ink` color used in light mode —
use near-white or amber, whichever fits the rest of dark mode better.
Active item must always be clearly distinguishable from inactive, in
both themes.

FIX B — Dark mode toggle track invisible when ON: set the ON-state
track explicitly to the amber token regardless of light/dark mode, so
it's always visible (not just a floating thumb with no visible track).

FIX C — "Next"/primary button has no fill: every primary CTA
(Next, Generate Report, Save, Upgrade to Pro, etc.) must have an
explicit `background-color: amber` fill, in both light and dark mode
— not just light text color that happens to be visible on some
backgrounds. Audit all instances, not just the one reported.

VERIFY: Push and deploy. Tell me to check both light and dark mode
live for: sidebar nav active state, Settings tabs, the dark mode
toggle track, and every primary button (Map Columns Next, Generate
Report, Save, Upgrade buttons).

**[STOP — get sign-off on Phase 0A and 0B before continuing. These are
regressions in shipped features.]**

---

## PHASE 1 — Signature brand motif/glyph + DESIGN_SYSTEM.md

First, create `DESIGN_SYSTEM.md` at the repo root documenting every
locked design decision so future prompts can reference this file
instead of having identity re-explained each time (this project has
had repeated drift — accent color applied inconsistently across
surfaces, font swaps silently breaking Unicode glyphs, dark mode
tokens inherited instead of explicit — a single source of truth
reduces this). Include:
- All font/color/token values from the "Locked identity reference"
  section above
- Rule: trend arrows are ALWAYS drawn vector triangles, never Unicode
  characters (font-glyph-coverage risk)
- Rule: dark mode colors are ALWAYS explicitly defined per component,
  never inherited/inverted from light mode values
- Rule: every primary CTA button must have an explicit background
  fill in both light and dark mode, not just a text color
- Rule: brand color in Settings > Branding is user-customizable and
  intentionally overrides the default amber in PDFs — never "fix" this
- A running list of every file/component that uses these tokens, to
  be updated as each phase below touches new files

Then design ONE simple recurring SVG symbol: a minimal ascending-bars
glyph (3-4 bars of increasing height) or a stylized mark incorporating
"N". Single amber color, transparent background, readable at 16px,
scalable to 200px. Apply to: favicon, browser tab icon, loading
spinner replacement.

Show the SVG at 16px/64px/200px before using it in later phases —
foundation for Phases 5, 6, 7.

---

## PHASE 2 — Tactile paper texture (PostHog-style, pushed harder)

Add a noise/grain texture overlay to the cream background — more
pronounced than a bare minimum subtle effect (reference: PostHog's
data-tool redesign uses visible vintage paper texture in data tables
to feel tactile and human-made, not flat/generic). Use SVG
feTurbulence filter or repeating noise texture, layered at low-but-
perceptible opacity (test 3-5%, pick what reads as "quality paper"
not "visual bug"). Apply to: main app background, PDF page background
(test if feasible without bloating file size — if not clean in PDF,
web app only).

Show before/after on the same page.

---

## PHASE 3 — Report generation loading animation

Replace the static checklist+spinner with 6 vertical bars (amber)
that grow in height as the 4 stages progress (Parsing → Charts → AI
insights → PDF), animating smoothly on each stage transition (~300ms
ease). Keep the existing 4-line text checklist with checkmarks BELOW
the animation — animation is decorative, the text checklist remains
the source of truth driven by real polling/status data.

---

## PHASE 4 — Count-up number animations

Add count-up animation (0 to final value, ~600-800ms ease-out) to
dashboard summary numbers and KPI hero numbers on report
load/completion. Respect `prefers-reduced-motion` — skip animation,
show final value immediately, for users with that setting.

---

## PHASE 5 — Empty state illustrations

Build a single-color outline SVG (amber strokes, matching Phase 1's
line weight) for "No reports yet": document outline with header lines
and small bar-chart bars, plus a small magnifying-glass accent. Pair
with: Fraunces title "No reports yet", one specific explanatory line
(not generic "no data" — explain the actual action: "Upload a CSV or
connect Google Sheets to generate your first client-ready PDF
report"), and a filled amber CTA button. Reuse this pattern (same
style, different icon) for other empty states (no API key, no
branding set, etc.).

---

## PHASE 6 — PDF cover page redesign

Before changing anything, show me current cover page code in
pdf_service.py.

Redesign to: thin amber rule (4px, ~48px wide) above title → small
uppercase report-type label (IBM Plex Mono) → Fraunces title, large →
hero stat as typographic focal point (large Fraunces number + the
Phase 0A drawn-triangle arrow + label stating what/when) → very faint
(4-5% opacity) Phase 1 motif watermark in bottom-right corner →
footer with "Prepared by [Name]" + date, separated by thin rule. ONE
accent color (amber) throughout, beyond the semantic red/mint trend
arrow.

VERIFY: Push and deploy. Generate a fresh test report and download
the real PDF so I can check the cover page myself.

---

## PHASE 7 — Landing page hero, asymmetric layout

Replace the centered-text hero with: headline + subtext + dual CTA on
the left (60%), a tilted (1-2deg) card on the right showing a
miniature mock of an actual generated report (small header band, hero
stat with drawn-triangle arrow, small bar chart) using the same PDF
cover visual language from Phase 6. Add a very subtle dot-grid texture
(4% opacity) behind the hero content. Nav: wordmark + Phase 1 motif
icon, Features/Pricing/How it works links, filled amber "Start Free"
button.

---

## PHASE 8 — Features section, bento grid

Replace the uniform 3-column feature grid with an asymmetric bento
layout: one large featured tile (2-wide, 2-tall) for the strongest
feature (AI Executive Summary), smaller tiles for secondary features.
Adjust grid spans to fit actual feature count. Each tile: line icon
(stroke, amber) + Fraunces title + 1-2 line description.

---

## PHASE 9 — Dashboard reports list

Replace the report card/grid with scannable rows: icon thumbnail,
report name + generation date, trend stat (mint/red), tier badge
(Free/Pro), Download action. Header: "Your Reports" (Fraunces) + one
prominent "+ New Report" CTA (filled amber), no competing secondary
buttons. If 0 reports, show Phase 5 empty state instead of an empty
list.

---

## FINAL VERIFICATION

After all phases: run full test suite, confirm 100% pass, push final
deploy. Update DESIGN_SYSTEM.md's file-list section with everything
touched across all phases. Give me a checklist of what to check live for each phase:
Phase 0A/0B fixes (light+dark), Phase 1 favicon/tab, Phase 2 texture,
Phase 3 generation animation (trigger a real report to see it), Phase
4 count-up (load the dashboard or finish a report), Phase 5 empty
state (view dashboard with 0 reports if possible, or describe how to
trigger it), Phase 6 PDF cover (download a fresh report), Phase 7
landing hero, Phase 8 bento features, Phase 9 dashboard list
(light+dark). grep the entire codebase for any remaining hardcoded
indigo/#6366F1/Space Grotesk references that might have been missed
and list anything found. Confirm Fraunces renders correctly (not
falling back to system serif) on at least 3 page types.

Do not skip deploy checkpoints between phases to save time — a real
deploy and live check catches things passing tests don't.
