"""Optional observability bootstrap: Sentry (errors) + OpenTelemetry (tracing).

Both are no-ops unless their env vars are set, so dev/test are unaffected and
nothing imports a heavy SDK unless configured. Production enables them by
setting SENTRY_DSN and OTEL_EXPORTER_OTLP_ENDPOINT (any OTLP collector —
e.g. an OpenTelemetry Collector, Grafana Alloy, or Azure Monitor via the
collector's OTLP receiver).

Vendor choices are deliberate defaults, not hard couplings: OTel exports to
whatever collector you point it at, and Sentry can be swapped for any SDK that
reads SENTRY_DSN. Both are additive.
"""
import logging
import os

logger = logging.getLogger(__name__)


def setup_observability(app=None) -> None:
    """Initialise Sentry + OTel if configured. Safe to call at import time."""
    _setup_sentry()
    _setup_tracing()


def _setup_sentry() -> None:
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return
    try:
        import sentry_sdk
    except ImportError:  # pragma: no cover - env var set without the dep
        logger.warning("SENTRY_DSN set but sentry-sdk not installed; skipping.")
        return
    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("APP_ENV", "dev"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        send_default_pii=False,  # PII (participant names) stays out of Sentry
    )
    logger.info("Sentry initialised (env=%s).", os.getenv("APP_ENV", "dev"))


def _setup_tracing() -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:  # pragma: no cover - env var set without the deps
        logger.warning(
            "OTEL_EXPORTER_OTLP_ENDPOINT set but opentelemetry exporter not installed; skipping."
        )
        return
    resource = Resource.create(
        {"service.name": os.getenv("OTEL_SERVICE_NAME", "workshop-tool-api")}
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
    logger.info("OpenTelemetry tracing initialised (endpoint=%s).", endpoint)
