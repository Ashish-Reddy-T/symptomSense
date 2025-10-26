#!/usr/bin/env bash
set -euo pipefail

if [ -f "scripts/warm_start.py" ]; then
  echo "[entrypoint] Running warm_start.py"
  python scripts/warm_start.py || echo "[entrypoint] warm_start.py failed, continuing"
fi

exec "$@"
