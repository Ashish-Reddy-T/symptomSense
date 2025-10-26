"""Tracing helpers (optional)."""

from __future__ import annotations

import logging

from ..core.settings import Settings

logger = logging.getLogger(__name__)


def setup_tracing(_: Settings) -> None:
    """Initialise tracing if OpenTelemetry environment variables are present.

    The hackathon environment might not provide an OTLP collector, so this is a no-op
    placeholder that can be expanded easily.
    """

    # Intentionally left as a stub to avoid importing heavy OTEL dependencies during the hackathon.
    logger.debug("tracing_not_configured")
