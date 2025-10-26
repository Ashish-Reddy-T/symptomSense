"""Export Prometheus metrics snapshot."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.telemetry.metrics import latest_metrics


def export(output: str = "metrics.prom") -> Path:
    data = latest_metrics()
    path = Path(output)
    path.write_bytes(data)
    return path


if __name__ == "__main__":
    target = export()
    print(f"Metrics written to {target}")
