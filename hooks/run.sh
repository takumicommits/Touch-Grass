#!/usr/bin/env bash
# Runs a Touch Grass Python script with whichever Python 3 this machine has (python3, python, or py on Windows).
# Without Python the hooks step aside quietly (exit 0), so Claude Code keeps working.
# Set GRASS_REQUIRE_PYTHON=1 to get exit code 3 and a message instead (used by /grass:setup).
for py in python3 python py; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >/dev/null 2>&1; then
    exec "$py" "$@"
  fi
done
if [ "${GRASS_REQUIRE_PYTHON:-}" = "1" ]; then
  echo "PYTHON_MISSING: Touch Grass needs Python 3.8 or newer." >&2
  exit 3
fi
exit 0
