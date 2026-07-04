"""SSE (Server-Sent Events) stream for live session updates.

Clients subscribe with GET /sessions/{session_id}/ideas/stream and receive a
continuous event stream: idea_added, idea_voted, participant_joined. Used by
the Flutter participant + facilitator UIs for the "live workshop" feel.

See app/services/event_bus.py for the in-memory bus this reads from.
"""

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession

from app.dependencies import _extract_bearer, get_db, get_event_bus, resolve_principal
from app.services.event_bus import EventBusProtocol

logger = logging.getLogger(__name__)

router = APIRouter(tags=["stream"])


@router.get("/sessions/{session_id}/ideas/stream")
async def idea_stream(
    session_id: str,
    token: str | None = Query(default=None, description="Participant or facilitator bearer token (web/EventSource path)."),
    authorization: str | None = Header(default=None),
    db: DBSession = Depends(get_db),
    bus: EventBusProtocol = Depends(get_event_bus),
):
    """Stream live session events as Server-Sent Events.

    Authenticated. The token is accepted from EITHER the query string OR the
    Authorization header: web's EventSource can't set headers (so it uses
    ``?token=``), while mobile/desktop (Dio) send a header to keep the token
    out of URLs/proxy logs. Both resolve to the same [resolve_principal].
    """
    tok = token
    if not tok and authorization:
        tok = _extract_bearer(authorization)  # raises AuthError on a malformed header
    # resolve_principal raises AuthenticationError (401) or SessionNotFoundError (404).
    resolve_principal(session_id, tok, db)

    queue = await bus.subscribe(session_id)

    async def event_generator():
        # Drop the DB session — we don't need it across the long-lived stream.
        db.close()
        try:
            # Initial heartbeat so the client knows the stream is alive.
            yield ": connected\n\n"
            while True:
                try:
                    # Block waiting for an event, with a periodic heartbeat
                    # so proxies don't kill idle connections. 5s (not 15s)
                    # because mobile browsers buffer until frequent flushes.
                    payload = await asyncio.wait_for(queue.get(), timeout=5.0)
                    data = json.dumps(payload, default=str)
                    # No `event:` field: the event type is carried in the JSON
                    # payload's "type" key (parsed by SseEvent.fromJson). Per the
                    # SSE spec, a frame WITHOUT an event: field dispatches a
                    # generic "message" event — which is what EventSource.onMessage
                    # listens for on web. Adding `event: idea_added` here would
                    # route to a *named* listener and skip onMessage entirely,
                    # so the web client would connect but never fire. The mobile
                    # (Dio) client parses the data: line directly and ignores the
                    # event: field either way.
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            logger.debug("SSE client disconnected for session %s", session_id)
            raise
        finally:
            await bus.unsubscribe(session_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            # Disable proxy/browser buffering so events flush immediately.
            # no-transform defeats mobile carriers' compression proxies that
            # buffer SSE; no-cache stops browser caching of the stream.
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
