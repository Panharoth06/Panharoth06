"""Shared field-report typography helpers.

Text is shaped with HarfBuzz and converted to SVG paths, so every
generated plate is self-contained and font-independent at render time.
"""

from __future__ import annotations

import re
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
REPO_FONTS = ROOT / "assets" / "src" / "fonts"
SKILL_FONTS = Path.home() / ".agents" / "skills" / "canvas-design" / "canvas-fonts"
FONT_DIR = REPO_FONTS if (REPO_FONTS / "Gloock-Regular.ttf").exists() else SKILL_FONTS

DISPLAY = FONT_DIR / "Gloock-Regular.ttf"
MONO = FONT_DIR / "IBMPlexMono-Regular.ttf"
SANS = FONT_DIR / "InstrumentSans-Regular.ttf"
SANS_BOLD = FONT_DIR / "InstrumentSans-Bold.ttf"

NUM = re.compile(r"-?\d+\.\d+")


def round_path(d: str) -> str:
    return NUM.sub(lambda m: f"{float(m.group()):.1f}", d)


def text_path(
    font_path: Path,
    text: str,
    size: float,
    *,
    x: float,
    y: float,
    tracking: float = 0.0,
    anchor: str = "start",
) -> tuple[str, float]:
    blob = hb.Blob.from_file_path(str(font_path))
    face = hb.Face(blob)
    hb_font = hb.Font(face)
    upem = face.upem

    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb_font, buf, {"kern": True, "liga": True})

    infos = buf.glyph_infos
    positions = buf.glyph_positions
    scale = size / upem

    width = sum(p.x_advance for p in positions) * scale
    width += tracking * max(0, len(infos) - 1)

    if anchor == "end":
        x -= width
    elif anchor == "middle":
        x -= width / 2

    tt = TTFont(str(font_path))
    glyph_set = tt.getGlyphSet()
    order = tt.getGlyphOrder()

    pen_x = x
    parts: list[str] = []
    for info, pos in zip(infos, positions):
        name = order[info.codepoint]
        pen = SVGPathPen(glyph_set)
        tx = pen_x + pos.x_offset * scale
        ty = y - pos.y_offset * scale
        glyph_set[name].draw(TransformPen(pen, (scale, 0, 0, -scale, tx, ty)))
        d = pen.getCommands()
        if d:
            parts.append(round_path(d))
        pen_x += pos.x_advance * scale + tracking

    return " ".join(parts), width
