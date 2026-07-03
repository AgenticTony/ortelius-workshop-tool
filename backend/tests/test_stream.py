"""Tests for the SSE real-time layer.

The stream endpoint itself is long-lived and hard to test deterministically
through the HTTP layer in-process (the async generator + heartbeat loop and
the test event loop interact awkwardly, and it hangs). So we test:

1. The event bus directly — subscribe, publish, receive on the queue, and
   verify unsubscribe cleans up. This is where the real logic lives.
2. The stream endpoint's error path (404 for unknown session) only.

End-to-end "POST an idea and see it on the wire" is verified manually via
curl against the running container (see the verification step in the roadmap).
"""

import asyncio

import pytest
import httpx

from app.main import app
from app.services.event_bus import event_bus, EVENT_IDEA_ADDED


# ── Event bus unit tests ─────────────────────────────────────


@pytest.mark.asyncio
async def test_event_bus_subscribe_and_publish():
    """A subscribed queue receives the event that is published."""
    event_bus.set_loop(asyncio.get_running_loop())
    queue = await event_bus.subscribe("session-1")
    try:
        event_bus.publish("session-1", EVENT_IDEA_ADDED, {"id": "idea-99"})
        # publish schedules the put via call_soon_threadsafe on the running
        # loop, so yield once to let it land.
        payload = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert payload["type"] == EVENT_IDEA_ADDED
        assert payload["data"]["id"] == "idea-99"
    finally:
        await event_bus.unsubscribe("session-1", queue)


@pytest.mark.asyncio
async def test_event_bus_unsubscribe_removes_queue():
    """After unsubscribe, the queue is gone from the registry."""
    event_bus.set_loop(asyncio.get_running_loop())
    queue = await event_bus.subscribe("session-2")
    assert "session-2" in event_bus._subscribers
    await event_bus.unsubscribe("session-2", queue)
    assert "session-2" not in event_bus._subscribers


@pytest.mark.asyncio
async def test_event_bus_publish_no_subscribers_is_noop():
    """Publishing with no subscribers must not raise."""
    event_bus.set_loop(asyncio.get_running_loop())
    event_bus.publish("no-such-session", EVENT_IDEA_ADDED, {"id": "x"})


@pytest.mark.asyncio
async def test_event_bus_multiple_subscribers_each_receive():
    """Every subscriber of a session gets the event."""
    event_bus.set_loop(asyncio.get_running_loop())
    q1 = await event_bus.subscribe("session-3")
    q2 = await event_bus.subscribe("session-3")
    try:
        event_bus.publish("session-3", EVENT_IDEA_ADDED, {"id": "shared"})
        p1 = await asyncio.wait_for(q1.get(), timeout=1.0)
        p2 = await asyncio.wait_for(q2.get(), timeout=1.0)
        assert p1["data"]["id"] == "shared"
        assert p2["data"]["id"] == "shared"
    finally:
        await event_bus.unsubscribe("session-3", q1)
        await event_bus.unsubscribe("session-3", q2)


# ── Stream endpoint: error path only ─────────────────────────


@pytest.mark.asyncio
async def test_stream_session_not_found():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        r = await async_client.get("/sessions/doesnotexist/ideas/stream")
        assert r.status_code == 404
