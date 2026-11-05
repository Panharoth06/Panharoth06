#!/usr/bin/env python3
"""Build the site's hidden icon sprite from assets/src/icons.json.

The same manifest is read by build-plates.py to outline icons directly into
the README stack plate.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "assets" / "src" / "icons.json"
OUT = ROOT / "docs" / "icons.svg"


def main() -> None:
    icons = json.loads(MANIFEST.read_text(encoding="utf-8"))
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">',
        "  <defs>",
    ]

    for key, icon in icons.items():
        width, height = icon["viewBox"]
        paths = "".join(f'<path d="{d}"/>' for d in icon["paths"])
        if width == height and width != 24:
            paths = f'<g transform="scale({24 / width:.6f})">{paths}</g>'
        lines.append(f'    <symbol id="icon-{key}" viewBox="0 0 24 24">{paths}</symbol>')

    lines += ["  </defs>", "</svg>", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}  {len(icons)} icons")


if __name__ == "__main__":
    main()
