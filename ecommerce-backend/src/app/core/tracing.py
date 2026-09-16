import socket

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("tracing")
settings = get_settings()


def _is_endpoint_reachable(endpoint: str, timeout: float = 2.0) -> bool:
    host, _, port = endpoint.partition(":")
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except (OSError, ValueError):
        return False


def configure_tracing(app, engine) -> None:
    resource = Resource.create({"service.name": settings.app_name})
    provider = TracerProvider(resource=resource)

    if _is_endpoint_reachable(settings.otel_exporter_endpoint):
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        logger.info("opentelemetry_configured", endpoint=settings.otel_exporter_endpoint)
    else:
        trace.set_tracer_provider(provider)
        logger.warning("opentelemetry_skipped", endpoint=settings.otel_exporter_endpoint, reason="unreachable")

    try:
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    except Exception as e:
        logger.warning("sqlalchemy_instrumentation_skipped", error=str(e))