#!/usr/bin/env python3
"""
Render the profile intro card that sits beside ascii.svg.

The copy below is the source of truth. This card does not read contribution
data. The daily workflow refreshes only the contribution graph, so a cron run
cannot overwrite this card with stats or with another product name.

    python scripts/render_stats_svg.py [output.svg]

Canvas matches ascii.svg (840 x 880) so equal README widths line the two up.
Name and role are visible immediately. Detail rows fade in once and hold.
"""
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "info-card.svg")

BG = "#151515"
INK = "#F5F5F5"
LABEL = "#A1A1AA"
ACCENT = "#5C40E8"
FRAME = "#2A2A2A"

W, H = 840, 880
TITLEBAR_H = 36
PAD_X = 56
LABEL_X = PAD_X
VALUE_X = 268
NAME_SIZE = 56
ROLE_SIZE = 34
ROW_SIZE = 32
LINE_H = 46

# (label, value lines, accent the value)
# Long values are wrapped here so the type stays readable inside the canvas.
ROWS = [
    ("Building", ["TETRAPOD"], True),
    ("Focus", ["On-Premises AI ·", "Multi-Agent Systems"], False),
    ("Stack", ["Python · Next.js ·", "PostgreSQL"], False),
    ("Approach", ["From ideas to", "deployed products."], False),
    ("Location", ["South Korea"], False),
]

ROW_STAGGER = 0.42
REVEAL_DUR = 0.55
FIRST_DELAY = 0.35


def esc(text):
    return html.escape(text, quote=False)


parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
    f'viewBox="0 0 {W} {H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    "<style>"
    ".row{opacity:0;animation:reveal "
    f"{REVEAL_DUR}s ease-out both}}"
    "@keyframes reveal{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}"
    "@media (prefers-reduced-motion: reduce){"
    ".row{opacity:1!important;transform:none!important;animation:none!important}}"
    "</style>",
    f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>',
    f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD_X + i * 18}" cy="{TITLEBAR_H / 2}" r="5.5" fill="{dot}"/>')
parts.append(
    f'<text x="{W / 2}" y="{TITLEBAR_H / 2 + 5}" fill="{LABEL}" font-size="16" '
    f'text-anchor="middle">rhtmdgks@github: ~$ ./whoami.sh</text>'
)

# Identity stays put. Detail rows below it are the only animated elements.
name_y = 168
role_y = name_y + 58
parts.append(
    f'<text x="{PAD_X}" y="{name_y}" fill="{INK}" font-size="{NAME_SIZE}" '
    f'font-weight="700">{esc("Edmond Ko")}</text>'
)
parts.append(
    f'<text x="{PAD_X}" y="{role_y}" fill="{INK}" font-size="{ROLE_SIZE}">'
    f'{esc("Founder & AI Engineer")}</text>'
)
rule_y = role_y + 36
parts.append(
    f'<rect x="{PAD_X}" y="{rule_y}" width="72" height="4" rx="2" fill="{ACCENT}"/>'
)

y = rule_y + 78
for i, (label, lines, accent) in enumerate(ROWS):
    delay = FIRST_DELAY + i * ROW_STAGGER
    value_fill = ACCENT if accent else INK
    parts.append(f'<g class="row" style="animation-delay:{delay:.2f}s">')
    parts.append(
        f'<text x="{LABEL_X}" y="{y}" fill="{LABEL}" font-size="{ROW_SIZE}">{esc(label)}</text>'
    )
    for j, line in enumerate(lines):
        parts.append(
            f'<text x="{VALUE_X}" y="{y + j * LINE_H}" fill="{value_fill}" '
            f'font-size="{ROW_SIZE}">{esc(line)}</text>'
        )
    parts.append("</g>")
    y += LINE_H * len(lines) + 28

parts.append("</svg>")
svg = "".join(parts)
with open(OUT, "w") as f:
    f.write(svg)
print(f"wrote {OUT}: {W} x {H}, last baseline {y - 28}, {len(svg)} bytes")
