"""Prometheus metrics helpers."""

from __future__ import annotations

import time

from prometheus_client import Counter, Histogram, generate_latest

REQUEST_LATENCY = Histogram(
    "agentic_api_latency_seconds",
    "API request latency in seconds",
    labelnames=["endpoint"],
)
REQUEST_TOTAL = Counter(
    "agentic_api_requests_total",
    "API requests processed",
    labelnames=["endpoint", "status"],
)


class RequestTracker:
    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self._start = time.perf_counter()

    def observe_success(self) -> None:
        self._observe("success")

    def observe_error(self) -> None:
        self._observe("error")

    def _observe(self, status: str) -> None:
        elapsed = time.perf_counter() - self._start
        REQUEST_LATENCY.labels(endpoint=self.endpoint).observe(elapsed)
        REQUEST_TOTAL.labels(endpoint=self.endpoint, status=status).inc()


def latest_metrics() -> bytes:
    return generate_latest()
