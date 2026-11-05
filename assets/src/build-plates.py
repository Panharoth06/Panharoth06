#!/usr/bin/env python3
"""Build the static Field Report plates for the profile README.

Outputs:
  assets/work-light.svg     assets/work-dark.svg
  assets/stack-light.svg    assets/stack-dark.svg
  assets/footer-light.svg   assets/footer-dark.svg

The activity plate is built separately, from live data, by build-activity.py.
"""

from __future__ import annotations

from fieldtype import DISPLAY, MONO, SANS, ROOT, text_path

W = 1280

THEMES = {
    "light": {
        "bg": "#E7E4DC",
        "ink": "#12161B",
        "muted": "#5B626B",
        "micro": "#4C535C",
        "accent": "#B23A2E",
        "grid": "rgba(18,22,27,0.055)",
        "rule": "rgba(18,22,27,0.18)",
        "soft": "rgba(18,22,27,0.09)",
    },
    "dark": {
        "bg": "#12161B",
        "ink": "#E7E4DC",
        "muted": "#9AA0A6",
        "micro": "#B4B8BC",
        "accent": "#D2493C",
        "grid": "rgba(231,228,220,0.05)",
        "rule": "rgba(231,228,220,0.20)",
        "soft": "rgba(231,228,220,0.10)",
    },
}


def label(text: str, size: float, x: float, y: float, fill: str, *,
          font=MONO, tracking: float = 0.0, anchor: str = "start") -> str:
    d, _ = text_path(font, text, size, x=x, y=y, tracking=tracking, anchor=anchor)
    return f'<path d="{d}" fill="{fill}"/>'


def measure(text: str, size: float, *, font=MONO, tracking: float = 0.0) -> float:
    _, width = text_path(font, text, size, x=0, y=0, tracking=tracking)
    return width


def wrap(text: str, size: float, max_width: float, *, font=SANS, tracking: float = 0.0) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if not current or measure(candidate, size, font=font, tracking=tracking) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def shell(palette: dict, height: int, title: str, desc: str,
          header_left: str, header_right: str) -> list[str]:
    accent = palette["accent"]
    muted = palette["muted"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" '
        f'width="{W}" height="{height}" role="img" aria-labelledby="t d">',
        f"  <title id=\"t\">{title}</title>",
        f"  <desc id=\"d\">{desc}</desc>",
        "  <defs>",
        f'    <pattern id="grid" x="72" y="24" width="64" height="64" patternUnits="userSpaceOnUse">',
        f'      <path d="M 64 0 V 64 M 0 64 H 64" fill="none" stroke="{palette["grid"]}" stroke-width="1"/>',
        "    </pattern>",
        "  </defs>",
        f'  <rect width="{W}" height="{height}" fill="{palette["bg"]}"/>',
        f'  <rect width="{W}" height="{height}" fill="url(#grid)"/>',
        f'  <g stroke="{muted}" stroke-width="1" fill="none" opacity="0.55">',
        '    <path d="M 30 44 V 30 H 44"/>',
        '    <path d="M 1236 30 H 1250 V 44"/>',
        f'    <path d="M 30 {height - 44} V {height - 30} H 44"/>',
        f'    <path d="M 1236 {height - 30} H 1250 V {height - 44}"/>',
        "  </g>",
        f'  <rect x="72" y="49" width="6" height="6" fill="{accent}"/>',
        label(header_left, 12, 88, 57, muted, tracking=2.4),
        label(header_right, 11.5, 1208, 57, muted, tracking=1.61, anchor="end"),
        f'  <line x1="72" y1="96" x2="1208" y2="96" stroke="{palette["rule"]}" stroke-width="1"/>',
    ]
    return parts


def work_plate(theme: str, palette: dict) -> str:
    height = 620
    ink = palette["ink"]
    muted = palette["muted"]
    accent = palette["accent"]
    soft = palette["soft"]

    entries = [
        (
            "raiwall",
            "Self-hosted web application firewall and reverse proxy, built as a Caddy module. "
            "OWASP CRS inspection, outbound DLP, rate limiting, and an embedded admin dashboard "
            "in one binary.",
            "GO · CADDY · VUE",
        ),
        (
            "Document verification",
            "Tamper-evident certificate issuance and verification. Playwright renders the "
            "document; a SHA-256 digest proves it has not changed since.",
            "JAVA 21 · SPRING BOOT · POSTGRESQL · PLAYWRIGHT",
        ),
        (
            "CodeCompass",
            "Algorithm-practice platform with automated judging, packages, badges, and "
            "leaderboards. Built by a small team I led.",
            "SPRING BOOT · NEXT.JS · POSTGRESQL",
        ),
    ]

    parts = shell(
        palette,
        height,
        "Selected work — raiwall, Document verification, CodeCompass",
        "Three public repositories set as Field Report entries.",
        "SELECTED WORK / 03 ENTRIES",
        "THREE PUBLIC REPOSITORIES",
    )

    for index, (name, note, stack) in enumerate(entries):
        top = 118 + index * 152
        parts.append(
            f'<line x1="72" y1="{top}" x2="1208" y2="{top}" stroke="{soft}" stroke-width="1"/>'
        )
        if index == 0:
            parts.append(
                f'<rect x="72" y="{top + 12}" width="2" height="56" fill="{accent}"/>'
            )
        parts.append(label(f"0{index + 1}", 10, 88, top + 48, muted, tracking=1.4))

        name_size = 44
        if measure(name, name_size, font=DISPLAY, tracking=-0.5) > 476:
            name_size = 38
        parts.append(
            label(name, name_size, 136, top + 56, ink, font=DISPLAY, tracking=-0.5)
        )

        note_lines = wrap(note, 16, 560)
        for line_index, line in enumerate(note_lines):
            parts.append(
                label(line, 16, 620, top + 34 + line_index * 22.5, ink, font=SANS)
            )

        parts.append(label(stack, 9.5, 620, top + 120, muted, tracking=1.5))

    parts.append(
        f'<line x1="72" y1="584" x2="1208" y2="584" stroke="{palette["rule"]}" stroke-width="1"/>'
    )
    parts.append(
        label("SOURCE LINKS IN THE FIELD INDEX BELOW", 8.5, 72, 602, muted, tracking=1.2)
    )
    parts.append(
        label("PANHAROTH06 / 2026", 8.5, 1208, 602, muted, tracking=1.2, anchor="end")
    )
    parts.append("</svg>")
    return "\n".join(parts)


def stack_plate(theme: str, palette: dict) -> str:
    height = 520
    ink = palette["ink"]
    muted = palette["muted"]
    soft = palette["soft"]

    groups = [
        ("BACKEND", "Java 21  ·  Spring Boot  ·  Spring Security  ·  Spring Data JPA  ·  Go  ·  gRPC  ·  REST"),
        ("FRONTEND", "TypeScript  ·  React  ·  Next.js  ·  Redux Toolkit  ·  Tailwind CSS"),
        ("DATA", "PostgreSQL  ·  Redis  ·  MongoDB  ·  MinIO"),
        ("INFRASTRUCTURE", "Docker  ·  Kubernetes  ·  Jenkins  ·  Nginx"),
        ("SECURITY", "OWASP Top 10  ·  JWT / OAuth2  ·  Keycloak  ·  HashiCorp Vault"),
    ]

    parts = shell(
        palette,
        height,
        "Stack — backend, frontend, data, infrastructure, security",
        "The current tools, grouped by layer.",
        "STACK / 05 GROUPS",
        "CURRENT TOOLS / 2026",
    )

    for index, (group, tech) in enumerate(groups):
        y = 150 + index * 70
        if index > 0:
            parts.append(
                f'<line x1="72" y1="{y - 34}" x2="1208" y2="{y - 34}" stroke="{soft}" stroke-width="1"/>'
            )
        parts.append(label(group, 10, 72, y, muted, tracking=1.8))

        size = 18
        if measure(tech, size, font=SANS, tracking=0.1) > 944:
            size = 16.5
        parts.append(label(tech, size, 240, y, ink, font=SANS, tracking=0.1))

    parts.append(
        f'<line x1="72" y1="470" x2="1208" y2="470" stroke="{palette["rule"]}" stroke-width="1"/>'
    )
    parts.append(label("FULL TEXT VERSION BELOW", 8.5, 72, 492, muted, tracking=1.2))
    parts.append(
        label("PANHAROTH06 / 05 GROUPS", 8.5, 1208, 492, muted, tracking=1.2, anchor="end")
    )
    parts.append("</svg>")
    return "\n".join(parts)


def footer_plate(theme: str, palette: dict) -> str:
    height = 240
    ink = palette["ink"]
    muted = palette["muted"]

    parts = shell(
        palette,
        height,
        "Open the live field report",
        "The closing plate, linking to the interactive field report.",
        "END OF PLATE / 001",
        "PANHAROTH06 / 2026",
    )

    parts.append(label("Open the live", 38, 72, 146, ink, font=DISPLAY, tracking=-0.4))
    parts.append(label("field report", 38, 72, 186, ink, font=DISPLAY, tracking=-0.4))
    parts.append(
        label("PANHAROTH06.GITHUB.IO", 11.5, 72, 216, muted, tracking=1.6)
    )

    parts.append(
        label("11.5564° N / 104.9282° E", 10, 1208, 146, muted, tracking=1.2, anchor="end")
    )
    parts.append(
        label("EMAIL / GITHUB IN THE INDEX BELOW", 9, 1208, 176, muted, tracking=1.2, anchor="end")
    )
    parts.append(
        label("PHNOM PENH, CAMBODIA", 9, 1208, 206, muted, tracking=1.2, anchor="end")
    )
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    out = ROOT / "assets"
    builders = {"work": work_plate, "stack": stack_plate, "footer": footer_plate}
    for name, builder in builders.items():
        for theme, palette in THEMES.items():
            svg = builder(theme, palette)
            path = out / f"{name}-{theme}.svg"
            path.write_text(svg, encoding="utf-8")
            print(f"{path.relative_to(ROOT)}  {len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
