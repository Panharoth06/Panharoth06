#!/usr/bin/env bash
# Build self-hosted WOFF2 subsets for the Field Report site.
# Source fonts: /Users/macbook/.agents/skills/canvas-design/canvas-fonts
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="$ROOT/assets/src/fonts"
if [ ! -f "$SRC/Gloock-Regular.ttf" ]; then
  SRC="$HOME/.agents/skills/canvas-design/canvas-fonts"
fi
OUT="$ROOT/docs/fonts"
UNICODES="U+0020-007E,U+00A0-00FF,U+2013-2014,U+2018-201D,U+2022,U+2026"

mkdir -p "$OUT"

subset() {
  local font="$1" out="$2"
  python3 -m fontTools.subset "$SRC/$font" \
    --output-file="$OUT/$out" \
    --flavor=woff2 \
    --unicodes="$UNICODES" \
    --layout-features='kern,liga,clig,calt,ccmp,mark,mkmk' \
    --desubroutinize \
    --no-hinting
  printf '%-28s %6s\n' "$out" "$(du -h "$OUT/$out" | cut -f1)"
}

subset Gloock-Regular.ttf            gloock-regular.woff2
subset IBMPlexMono-Regular.ttf       ibm-plex-mono-regular.woff2
subset InstrumentSans-Regular.ttf    instrument-sans-regular.woff2
subset InstrumentSans-Bold.ttf       instrument-sans-bold.woff2

cp "$ROOT/assets/src/fonts/OFL-Gloock.txt"          "$OUT/OFL-Gloock.txt"
cp "$ROOT/assets/src/fonts/OFL-IBMPlexMono.txt"     "$OUT/OFL-IBMPlexMono.txt"
cp "$ROOT/assets/src/fonts/OFL-InstrumentSans.txt"  "$OUT/OFL-InstrumentSans.txt"

echo "Fonts written to docs/fonts"
