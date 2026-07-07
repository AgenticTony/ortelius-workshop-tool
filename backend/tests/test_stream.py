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

import httpx
import pytest

from app.main import app
from app.services.event_bus import EVENT_IDEA_ADDED, event_bus

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


# ── Stream endpoint: error paths only ────────────────────────


@pytest.mark.asyncio
async def test_stream_requires_token():
    """No token at all (neither query nor header) → 401, not 422.

    The token is accepted from EITHER source (web query / mobile header); an
    entirely unauthenticated stream request is Unauthorized, not Unprocessable.
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        r = await async_client.get("/sessions/whatever/ideas/stream")
        assert r.status_code == 401


def test_stream_rejects_bad_token(client, sample_session):
    """A bogus token on a real session → 401."""
    r = client.get(
        f"/sessions/{sample_session['id']}/ideas/stream?token=not-a-real-token"
    )
    assert r.status_code == 401


def test_stream_accepts_token_via_authorization_header(client, sample_session):
    """Mobile/desktop send the token as an Authorization header (no ?token= query).

    The endpoint must read the header too — otherwise FastAPI returns 422
    (missing required query param) and live updates never open on non-web.
    A bogus header token must reach resolve_principal → 401, NOT 422.
    """
    r = client.get(
        f"/sessions/{sample_session['id']}/ideas/stream",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_stream_session_not_found(client, participant_headers):
    # Authenticated (valid token for another session) but the target session
    # doesn't exist → 404.
    token = participant_headers["Authorization"].split(" ", 1)[1]
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        r = await async_client.get(
            "/sessions/doesnotexist/ideas/stream", params={"token": token}
        )
        assert r.status_code == 404
