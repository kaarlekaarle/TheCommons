#!/usr/bin/env bash
set -euo pipefail

PY=${PY:-python3}
WHEELS_DIR="tools/offline_wheels"

# Prefer local wheels if present; otherwise try normal install (in case network exists)
if [ -d "$WHEELS_DIR" ] && [ -n "$(ls -A "$WHEELS_DIR" 2>/dev/null || true)" ]; then
  echo "Installing dev dependencies from local wheels..."
  $PY -m pip install --no-index --find-links "$WHEELS_DIR" -r requirements-dev.txt
else
  echo "No local wheels found. Attempting to install from index (may fail offline)..."
  $PY -m pip install -r requirements-dev.txt || {
    echo "Offline install failed and no wheels available. Please populate $WHEELS_DIR."
    exit 1
  }
fi
