"""Export Prometheus metrics snapshot."""

from __future__ import annotations

from pathlib import Path

from backend.app.telemetry.metrics import latest_metrics


def export(output: str = "metrics.prom") -> Path:
    data = latest_metrics()
    path = Path(output)
    path.write_bytes(data)
    return path


if __name__ == "__main__":
    target = export()
    print(f"Metrics written to {target}")
