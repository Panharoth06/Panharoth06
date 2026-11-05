#!/usr/bin/env python3
"""Build the animated Field Report hero as two self-contained SVGs.

Text is shaped with HarfBuzz and outlined with fontTools, so the hero
never depends on a font loading through GitHub's image proxy. GitHub
(Camo) caches by URL, so rename the outputs whenever the artwork changes.
"""

from __future__ import annotations

import math

from fieldtype import DISPLAY, MONO, ROOT, text_path

W, H = 1280, 400
CX, CY = 1073, 235
R_OUT = 131


THEMES = {
    "light": {
        "bg": "#E7E4DC",
        "ink": "#12161B",
        "muted": "#5B626B",
        "accent": "#B23A2E",
        "grid": "rgba(18,22,27,0.055)",
        "shine": "#FFF8EA",
        "shine_opacity": 0.80,
        "wash_opacity": 0.07,
    },
    "dark": {
        "bg": "#12161B",
        "ink": "#E7E4DC",
        "muted": "#9AA0A6",
        "accent": "#D2493C",
        "grid": "rgba(231,228,220,0.05)",
        "shine": "#FFF3DA",
        "shine_opacity": 0.68,
        "wash_opacity": 0.055,
    },
}


def build(theme: str, palette: dict, still: bool = False) -> str:
    ink = palette["ink"]
    muted = palette["muted"]
    accent = palette["accent"]
    shine = palette["shine"]
    shine_opacity = palette["shine_opacity"]
    wash_opacity = palette["wash_opacity"]

    name1, _ = text_path(DISPLAY, "Panharath", 98, x=64, y=210, tracking=-1.2)
    name2, _ = text_path(DISPLAY, "Chheng", 98, x=64, y=302, tracking=-1.2)
    eyebrow, _ = text_path(MONO, "FIELD NOTES / 001", 12, x=88, y=70, tracking=2.4)
    coords1, _ = text_path(
        MONO, "11.5564° N   104.9282° E", 11.5, x=1208, y=63, tracking=1.61, anchor="end"
    )
    coords2, _ = text_path(
        MONO, "PHNOM PENH, CAMBODIA", 11.5, x=1208, y=82, tracking=1.61, anchor="end"
    )
    role, _ = text_path(
        MONO,
        "FULL-STACK ENGINEER · SECURITY-MINDED",
        15,
        x=74,
        y=367,
        tracking=2.475,
    )

    # aperture ticks
    ticks: list[str] = []

    for i in range(72):
        angle = math.radians(i * 5)
        major = i % 18 == 0
        r1 = 120
        r2 = 131 if major else 127
        x1 = CX + math.cos(angle) * r1
        y1 = CY + math.sin(angle) * r1
        x2 = CX + math.cos(angle) * r2
        y2 = CY + math.sin(angle) * r2
        op = 0.38 if major else 0.20
        delay = 1.15 + i * 0.006
        ticks.append(
            f'<line class="tick" x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{ink}" stroke-width="{1.1 if major else 0.7}" opacity="{op}" '
            f'style="--o:{op};animation-delay:{delay:.3f}s"/>'
        )

    rings = [
        (31, 0.32, 0.00),
        (52, 0.26, 0.08),
        (74, 0.22, 0.16),
        (96, 0.18, 0.24),
        (118, 0.15, 0.32),
    ]
    ring_svg = "\n".join(
        f'<circle class="ring" cx="{CX}" cy="{CY}" r="{r}" fill="none" stroke="{ink}" '
        f'stroke-width="1" opacity="{op}" style="animation-delay:{d:.2f}s"/>'
        for r, op, d in rings
    )

    node_svg = f"""
    <g class="nodes">
      <circle cx="{CX - 56.7:.1f}" cy="{CY - 47.6:.1f}" r="2.4" fill="{ink}" opacity="0.45"/>
      <circle cx="{CX - 32.8:.1f}" cy="{CY + 90.2:.1f}" r="2.4" fill="{ink}" opacity="0.45"/>
      <circle cx="{CX + 39.8:.1f}" cy="{CY - 33.4:.1f}" r="2.4" fill="{ink}" opacity="0.45"/>
      <circle class="pulse" cx="{CX}" cy="{CY - 131}" r="10" fill="none" stroke="{accent}" stroke-width="0.8"/>
      <circle cx="{CX}" cy="{CY - 131}" r="3.2" fill="{accent}"/>
      <rect x="{CX - 3.4}" y="{CY - 3.4}" width="6.8" height="6.8" fill="{ink}" opacity="0.75" transform="rotate(45 {CX} {CY})"/>
    </g>"""

    # scan wedge: 34 degrees, from the outer radius to the centre
    a1, a2 = math.radians(-90), math.radians(-56)
    wedge = (
        f'M {CX} {CY} L {CX + math.cos(a1) * R_OUT:.2f} {CY + math.sin(a1) * R_OUT:.2f} '
        f'A {R_OUT} {R_OUT} 0 0 1 {CX + math.cos(a2) * R_OUT:.2f} {CY + math.sin(a2) * R_OUT:.2f} Z'
    )

    wave_defs = ""
    wave_wash = ""
    wave_shine = ""
    if not still:
        wave_defs = f"""
    <linearGradient id="waveFade" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="{H}">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/>
      <stop offset="0.42" stop-color="#fff" stop-opacity="0"/>
      <stop offset="0.465" stop-color="#fff" stop-opacity="0.55"/>
      <stop offset="0.5" stop-color="#fff" stop-opacity="0.95"/>
      <stop offset="0.535" stop-color="#fff" stop-opacity="0.55"/>
      <stop offset="0.58" stop-color="#fff" stop-opacity="0"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
      <animateTransform attributeName="gradientTransform" type="translate"
        values="-1500 -470; 1500 470; 1500 470" keyTimes="0;0.51;1"
        dur="7s" begin="2.4s" repeatCount="indefinite"/>
    </linearGradient>
    <mask id="waveMask" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
      <rect x="-600" y="-600" width="2480" height="1600" fill="url(#waveFade)"/>
    </mask>
    <filter id="waveGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="6"/>
    </filter>
    """
        wave_wash = (
            f'<rect class="wave-wash" width="{W}" height="{H}" fill="{shine}" '
            f'opacity="{wash_opacity}" mask="url(#waveMask)"/>'
        )
        wave_shine = f"""
  <g class="wave-shine" mask="url(#waveMask)" fill="{shine}" opacity="{shine_opacity}">
    <g filter="url(#waveGlow)" opacity="0.8">
      <path d="{name1}"/>
      <path d="{name2}"/>
    </g>
    <path d="{name1}" stroke="{shine}" stroke-width="0.7"/>
    <path d="{name2}" stroke="{shine}" stroke-width="0.7"/>
    <line x1="74" y1="330.5" x2="136" y2="330.5" stroke="{shine}" stroke-width="2" opacity="0.45"/>
    <path d="{role}"/>
    <g fill="none" stroke="{shine}" stroke-width="0.9" opacity="0.5">
      <circle cx="{CX}" cy="{CY}" r="31"/>
      <circle cx="{CX}" cy="{CY}" r="52"/>
      <circle cx="{CX}" cy="{CY}" r="74"/>
      <circle cx="{CX}" cy="{CY}" r="96"/>
      <circle cx="{CX}" cy="{CY}" r="118"/>
    </g>
    <g opacity="0.45">
      <path d="{eyebrow}"/>
      <path d="{coords1}"/>
      <path d="{coords2}"/>
    </g>
  </g>"""

    motion_css = f"""
    .grid, .fade {{ animation: fade 0.9s ease-out both; }}
    .l1 {{ animation: rise 1.15s cubic-bezier(.22,1,.36,1) .45s both; }}
    .l2 {{ animation: rise 1.15s cubic-bezier(.22,1,.36,1) .62s both; }}
    .rule {{ stroke-dasharray: 62; animation: draw 0.85s cubic-bezier(.22,1,.36,1) 1.05s both; }}
    .ring {{ stroke-dasharray: 900; animation: ring 1.5s cubic-bezier(.22,1,.36,1) both; }}
    .tick {{ animation: tick 0.7s ease-out both; }}
    .spin {{ animation: spin 180s linear 2.6s infinite; transform-origin: {CX}px {CY}px; }}
    .sweep {{ animation: sweep 9s cubic-bezier(.4,0,.2,1) 3.2s infinite; transform-origin: {CX}px {CY}px; opacity: 0; }}
    .pulse {{ transform-box: fill-box; transform-origin: center; animation: pulse 6s ease-out 4s infinite; opacity: 0; }}
    @keyframes fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    @keyframes rise {{ from {{ opacity: 0; transform: translateY(13px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes draw {{ from {{ stroke-dashoffset: 62; }} to {{ stroke-dashoffset: 0; }} }}
    @keyframes ring {{ from {{ stroke-dashoffset: 900; opacity: 0; }} to {{ stroke-dashoffset: 0; }} }}
    @keyframes tick {{ from {{ opacity: 0; }} to {{ opacity: var(--o); }} }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    @keyframes sweep {{
      0%, 54% {{ transform: rotate(0deg); opacity: 0; }}
      60% {{ opacity: 1; }}
      92% {{ opacity: 1; }}
      100% {{ transform: rotate(360deg); opacity: 0; }}
    }}
    @keyframes pulse {{
      0% {{ transform: scale(1); opacity: 0.55; }}
      38%, 100% {{ transform: scale(2.3); opacity: 0; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .grid, .fade, .l1, .l2, .rule, .ring, .tick, .spin, .sweep, .pulse {{ animation: none !important; }}
      .sweep, .pulse, .wave-wash, .wave-shine {{ display: none; }}
    }}
    """
    css = ".sweep, .pulse { display: none; }" if still else motion_css

    desc = (
        "A field-report plate: name set in a high-contrast serif, coordinates of "
        "Phnom Penh, and a still aperture diagram."
        if still
        else "A field-report plate: name set in a high-contrast serif, coordinates of "
        "Phnom Penh, a slow scanning aperture diagram, and a raking light that crosses the plate."
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">Panharath Chheng — full-stack engineer, security-minded</title>
  <desc id="d">{desc}</desc>
  <style>{css}</style>
  <defs>
    <pattern id="grid" x="72" y="24" width="64" height="64" patternUnits="userSpaceOnUse">
      <path d="M 64 0 V 64 M 0 64 H 64" fill="none" stroke="{palette['grid']}" stroke-width="1"/>
    </pattern>
    {wave_defs}
  </defs>

  <rect width="{W}" height="{H}" fill="{palette['bg']}"/>
  <rect class="grid" width="{W}" height="{H}" fill="url(#grid)"/>
  {wave_wash}

  <g stroke="{muted}" stroke-width="1" fill="none" opacity="0.55">
    <path d="M 30 44 V 30 H 44"/>
    <path d="M 1236 30 H 1250 V 44"/>
    <path d="M 30 356 V 370 H 44"/>
    <path d="M 1236 370 H 1250 V 356"/>
  </g>

  <g class="fade" style="animation-delay:.15s">
    <rect x="72" y="62" width="6" height="6" fill="{accent}"/>
    <path d="{eyebrow}" fill="{muted}"/>
  </g>

  <g class="fade" style="animation-delay:.3s">
    <path d="{coords1}" fill="{muted}"/>
    <path d="{coords2}" fill="{muted}"/>
  </g>

  <g class="l1"><path d="{name1}" fill="{ink}"/></g>
  <g class="l2"><path d="{name2}" fill="{ink}"/></g>

  <line class="rule" x1="74" y1="330.5" x2="136" y2="330.5" stroke="{accent}" stroke-width="2"/>

  <g class="fade" style="animation-delay:1.25s">
    <path d="{role}" fill="{ink}"/>
  </g>

  <g class="spin">
    {ring_svg}
    <circle cx="{CX}" cy="{CY}" r="{R_OUT}" fill="none" stroke="{ink}" stroke-width="1" opacity="0.36" stroke-dasharray="1 5"/>
    <line x1="{CX - R_OUT}" y1="{CY}" x2="{CX + R_OUT}" y2="{CY}" stroke="{ink}" stroke-width="0.6" opacity="0.10"/>
    <line x1="{CX}" y1="{CY - R_OUT}" x2="{CX}" y2="{CY + R_OUT}" stroke="{ink}" stroke-width="0.6" opacity="0.10"/>
    {"".join(ticks)}
  </g>

  <g class="sweep">
    <path d="{wedge}" fill="{accent}" opacity="0.06"/>
    <path d="M {CX} {CY} L {CX + math.cos(a1) * R_OUT:.2f} {CY + math.sin(a1) * R_OUT:.2f}" stroke="{accent}" stroke-width="0.8" opacity="0.28"/>
  </g>

  {node_svg}
  {wave_shine}
</svg>
"""
    return svg


def main() -> None:
    out = ROOT / "assets"
    for theme, palette in THEMES.items():
        for still in (False, True):
            svg = build(theme, palette, still=still)
            suffix = "-still" if still else ""
            path = out / f"hero-{theme}{suffix}.svg"
            path.write_text(svg, encoding="utf-8")
            print(f"{path.relative_to(ROOT)}  {len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
