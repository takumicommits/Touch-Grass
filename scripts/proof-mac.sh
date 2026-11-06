#!/bin/bash
# Launch (or focus) a Mac app and screenshot its window as proof.
# Usage: proof-mac.sh "<App name or /path/to/App.app>" [output.png]
# Prints the path of the saved screenshot.
set -u
APP="${1:?usage: proof-mac.sh <App name or .app path> [out.png]}"
OUT="${2:-.claude/proof/$(date +%Y%m%d-%H%M%S).png}"
DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$(dirname "$OUT")"

if [[ "$APP" == *.app || -d "$APP" ]]; then
  open "$APP"; NAME="$(basename "$APP" .app)"
else
  open -a "$APP"; NAME="$APP"
fi
sleep 3

WID="$(swift "$DIR/window-id.swift" "$NAME" 2>/dev/null || true)"
if [[ -n "$WID" ]]; then
  screencapture -x -o -l"$WID" "$OUT"
else
  echo "👀 couldn't find a window for '$NAME', captured the whole screen" >&2
  screencapture -x "$OUT"
fi
echo "$OUT"
