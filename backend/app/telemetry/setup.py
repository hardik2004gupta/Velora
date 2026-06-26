"""
OpenTelemetry bootstrap.

Instruments FastAPI, SQLAlchemy, and Redis when ``OTEL_ENABLED=true``.
When disabled (default in development), this is a no-op so there is zero
overhead and no dependency on an OTLP collector.

In production, set::

    OTEL_ENABLED=true
    OTEL_EXPORTER_OTLP_ENDPOINT=http://your-collector:4317
    OTEL_SERVICE_NAME=velora-backend
"""

from __future__ import annotations

from app.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


def setup_telemetry() -> None:
    """
    Bootstrap OpenTelemetry instrumentation.

    This function is called once from the FastAPI lifespan handler.
    If ``OTEL_ENABLED`` is False, it logs a notice and returns immediately.
    """
    settings = get_settings()

    if not settings.otel_enabled:
        log.info("telemetry_disabled", reason="OTEL_ENABLED=false")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({SERVICE_NAME: settings.otel_service_name})
        provider = TracerProvider(resource=resource)

        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor().instrument()
        SQLAlchemyInstrumentor().instrument()
        RedisInstrumentor().instrument()

        log.info(
            "telemetry_enabled",
            service=settings.otel_service_name,
            endpoint=settings.otel_exporter_otlp_endpoint,
        )

    except ImportError as exc:
        log.warning("telemetry_setup_failed", error=str(exc))
