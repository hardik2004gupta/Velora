"""
Structured logging via Structlog.

All logs are emitted as JSON in production and as coloured console output in
development.  Every log event automatically includes:

- ``timestamp`` — ISO-8601 UTC
- ``level`` — log level string
- ``logger`` — dotted module name
- ``request_id`` — injected by ``RequestIDMiddleware``
- ``trace_id`` — OpenTelemetry trace ID (placeholder until OTel is active)

Usage::

    import structlog

    log = structlog.get_logger(__name__)
    log.info("provider_selected", provider="openai", model="gpt-4o-mini")
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor


def _add_app_name(
    logger: Any,  # noqa: ANN401
    method: str,
    event_dict: EventDict,
) -> EventDict:
    """Inject the application name into every log record."""
    event_dict["app"] = "velora"
    return event_dict


def _drop_color_message_key(
    logger: Any,  # noqa: ANN401
    method: str,
    event_dict: EventDict,
) -> EventDict:
    """Remove the internal ``color_message`` key added by uvicorn."""
    event_dict.pop("color_message", None)
    return event_dict


def configure_logging(log_level: str = "INFO", *, json_logs: bool = True) -> None:
    """
    Configure Structlog for the application.

    Call once during application startup (inside the lifespan handler).

    Args:
        log_level: Python logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_logs: Emit JSON-formatted logs if True; coloured console output if False.
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        _add_app_name,
        _drop_color_message_key,
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Apply to root logger so uvicorn / SQLAlchemy logs are also formatted
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Return a bound Structlog logger for the given module name.

    Prefer calling this at module level::

        log = get_logger(__name__)
    """
    return structlog.get_logger(name)  # type: ignore[return-value]
