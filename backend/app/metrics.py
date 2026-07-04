"""Prometheus metrics.

Vendor-neutral (``prometheus_client``), so any scraper — Prometheus, Grafana
Agent, Datadog, VictoriaMetrics — can consume ``GET /metrics``. Labels are kept
low-cardinality on purpose (route templates, not raw paths carrying ids) so the
metrics store can't be blown up by per-session cardinality.
"""
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# HTTP request count + latency, labelled by method and the matched route
# *template* (e.g. "/sessions/{session_id}") — never the raw URL.
HTTP_REQUESTS = Counter(
    "workshop_http_requests_total",
    "HTTP requests processed, by method/route/status.",
    ["method", "route", "status"],
)
HTTP_REQUEST_LATENCY = Histogram(
    "workshop_http_request_duration_seconds",
    "HTTP request handling latency, by method/route.",
    ["method", "route"],
)

# Claude (Anthropic) cost/health observability — one inc per API call attempt.
CLAUDE_CALLS = Counter(
    "workshop_claude_calls_total",
    "Claude API calls attempted (includes the bad-JSON retry).",
    ["framework", "model", "retry"],
)

# Live SSE fan-out load. No session_id label (would be unbounded cardinality);
# the total is enough for capacity/scale alerting.
SSE_SUBSCRIBERS = Gauge(
    "workshop_sse_subscribers",
    "Active in-memory SSE subscriber queues across all sessions.",
)

METRICS_CONTENT_TYPE = CONTENT_TYPE_LATEST


def metrics_body() -> bytes:
    """Serialize the current metric values for the /metrics endpoint."""
    return generate_latest()
