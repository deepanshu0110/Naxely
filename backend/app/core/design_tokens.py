INK = "#14131F"
PAPER = "#FAFAFC"
SLATE = "#F3F2F8"
INDIGO = "#6366F1"
AMBER = "#D97A34"
MINT = "#0E9F6E"

# Canonical brand color — matches the frontend accent token default.
# chart_service.py and pdf_service.py still carry their own hardcoded
# defaults (Phase 5 will wire them here).
BRAND_COLOR = INDIGO

# Font-family CSS value strings (quoted for values with spaces).
# Phase 1 loads the actual font files; Phase 5 registers them with
# ReportLab / matplotlib.
FONT_DISPLAY = "'Space Grotesk', sans-serif"
FONT_BODY = "'IBM Plex Sans', sans-serif"
FONT_MONO = "'IBM Plex Mono', monospace"
