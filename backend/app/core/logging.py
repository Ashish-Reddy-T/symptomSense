"""Logging utilities wrapping structlog."""

import logging
from typing import Any

import structlog


def configure_logging(level: str = "INFO", json_logs: bool = True) -> None:
    """Configure structlog + stdlib logging.

    Parameters
    ----------
    level:
        Minimum log level (string name).
    json_logs:
        Whether to emit JSON structured logs. Falls back to key-value text when
        structlog JSON renderer is unavailable.
    """

    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
