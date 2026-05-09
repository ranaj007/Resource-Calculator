# ── Colour palette (dark-terminal aesthetic) ────────────────────────────────
COLORS = {
    "bg":        "#1a1d23",
    "row_alt":   "#1f2330",
    "border":    "#2e3347",
    "key_fg":    "#7eb8da",   # cool blue  – key column
    "val_fg":    "#c8d6e5",   # near-white – value column
    "type_fgg":   "#6a9e6a",   # muted green – type badge
    "type_fgr":   "#d66a6a",   # muted red   – type badge (for errors)
    "header_bg": "#151820",
    "header_fg": "#4a90b8",
    "gbadge_bg":  "#1c2b1c",
    "rbadge_bg":  "#3b1c1c",
    "sel_bg":    "#25304a",
    "scroll":    "#2e3347",
}

FONT_MONO = "Consolas, 'Courier New', monospace"

QLineEdit_STYLE = f"""
    QLineEdit {{
        color: {COLORS['key_fg']};
        border: 1px solid {COLORS['border']};
        border-radius: 3px;
        font-family: {FONT_MONO};
        font-size: 10px;
        }}
"""

CHAR_WIDTH = 7  # approximate width of a character in pixels (for fixed-width font)