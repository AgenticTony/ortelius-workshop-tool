"""Smoke tests for the Prometheus metrics surface.

The counter/histogram/gauge are process-global singletons, so we assert on
presence and deltas rather than absolute values (other tests in the run also
bump the HTTP counter).
"""
import asyncio

import pytest
from prometheus_client import REGISTRY

from app.services.event_bus import event_bus


def _metric_value(name: str) -> float | None:
    """Read a metric's current value from the global registry (no labels)."""
    for metric in REGISTRY.collect():
        for sample in metric.samples:
            if sample.name == name:
                return sample.value
    return None


def test_metrics_endpoint_exposes_http_counter(client):
    """A request is counted; /metrics returns the counter by name."""
    client.get("/health")  # produce at least one observation
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "workshop_http_requests_total" in body
    assert "workshop_http_request_duration_seconds" in body
    # The /health hit should show up under the /health route label.
    assert 'route="/health"' in body


def test_unmatched_route_uses_sentinel_label(client):
    """A 404 on an unknown path must label as 'unmatched', not the raw URL.

    Using the raw path would let an attacker spam unique URLs to blow up the
    metrics cardinality (one Prometheus time series per labelset).
    """
    client.get("/definitely-not-a-route-%d" % 123456)
    body = client.get("/metrics").text
    assert 'route="unmatched"' in body
    assert "/definitely-not-a-route-" not in body


@pytest.mark.asyncio
async def test_sse_subscriber_gauge_tracks_subscribe_unsubscribe():
    """Subscribe bumps the gauge; unsubscribe returns it."""
    event_bus.set_loop(asyncio.get_running_loop())
    before = _metric_value("workshop_sse_subscribers") or 0
    queue = await event_bus.subscribe("metrics-gauge-session")
    try:
        after = _metric_value("workshop_sse_subscribers")
        assert after == before + 1
    finally:
        await event_bus.unsubscribe("metrics-gauge-session", queue)
    assert _metric_value("workshop_sse_subscribers") == before
