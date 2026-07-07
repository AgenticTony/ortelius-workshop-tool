"""In-memory pub/sub event bus for real-time session updates (SSE).

Each session gets a set of subscriber queues. Routes that mutate shared state
(idea added, idea voted, participant joined) publish an event; the SSE stream
endpoint subscribes a queue and forwards events to the client as they arrive.

LIMITATION: in-memory only. This works with a single uvicorn worker (the
prototype deployment). Scaling to multiple workers requires moving the bus
onto Postgres LISTEN/NOTIFY or an external broker (Redis pub/sub) — listed as
future work in docs/frontend-roadiness.md.

THREADING NOTE: FastAPI runs synchronous route handlers (``def``, not
``async def``) in a threadpool, so those threads have no running event loop.
We therefore capture the main event loop at startup and publish onto it with
``call_soon_threadsafe``. ``publish()`` must remain a sync function so the
route handlers don't have to await it.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Any, Final, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# Event type constants — keep in sync with the SSE client.
EVENT_IDEA_ADDED: Final[str] = "idea_added"
EVENT_IDEA_VOTED: Final[str] = "idea_voted"
EVENT_PARTICIPANT_JOINED: Final[str] = "participant_joined"

# Per-subscriber queue cap. A slow/stalled SSE client accumulates at most this
# many pending events; beyond it we drop the oldest (live state matters more
# than history — a client can re-sync via the REST list endpoints). This bounds
# memory over a long workshop instead of growing without limit.
MAX_SUBSCRIBER_QUEUE: Final[int] = 256


@runtime_checkable
class EventBusProtocol(Protocol):
    """The pub/sub contract the routes and SSE endpoint depend on.

    The default implementation ([EventBus]) is in-memory and therefore
    single-uvicorn-worker only. Multi-worker HA means implementing this
    interface against a shared broker — Redis pub/sub or Postgres
    LISTEN/NOTIFY — and wiring it via ``app.dependencies.get_event_bus``.
    Routes depend on this Protocol, not the concrete class, so that swap is
    config-only at the composition root.
    """

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None: ...
    async def subscribe(self, session_id: str) -> asyncio.Queue: ...
    async def unsubscribe(self, session_id: str, queue: asyncio.Queue) -> None: ...
    def publish(self, session_id: str, event_type: str, data: Any) -> None: ...


def _safe_put(queue: asyncio.Queue, payload: Any) -> None:
    """Bounded-queue put with drop-oldest backpressure.

    Runs on the event loop (scheduled via ``call_soon_threadsafe``). If the
    subscriber queue is full, drop the oldest pending event and retry; this
    keeps server memory bounded while preferring the freshest state.
    """
    try:
        queue.put_nowait(payload)
    except asyncio.QueueFull:
        try:
            queue.get_nowait()  # make room by dropping the oldest pending event
        except asyncio.QueueEmpty:
            pass
        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:
            logger.debug("SSE subscriber queue still full after drop; event dropped")


class EventBus:
    """In-memory async event bus keyed by session_id.

    Thread-safe: ``publish`` may be called from synchronous route handlers
    running in a worker thread; it schedules the queue puts on the main loop.
    """

    def __init__(self) -> None:
        # session_id -> set of subscriber queues.
        self._subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)
        # The main event loop, captured at startup (see ``set_loop``).
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Capture the main event loop. Called once at app startup."""
        self._loop = loop

    async def subscribe(self, session_id: str) -> asyncio.Queue:
        """Register a new subscriber queue for a session. Returns the queue."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=MAX_SUBSCRIBER_QUEUE)
        self._subscribers[session_id].add(queue)
        logger.debug("SSE subscriber added for session %s (%d total)", session_id, len(self._subscribers[session_id]))
        return queue

    async def unsubscribe(self, session_id: str, queue: asyncio.Queue) -> None:
        """Remove a subscriber queue. Safe to call if not subscribed."""
        subscribers = self._subscribers.get(session_id)
        if subscribers is not None:
            subscribers.discard(queue)
        if not self._subscribers.get(session_id):
            self._subscribers.pop(session_id, None)
        logger.debug("SSE subscriber removed for session %s", session_id)

    def publish(self, session_id: str, event_type: str, data: Any) -> None:
        """Broadcast an event to all subscribers of a session.

        Synchronous and safe to call from sync route handlers (which run in
        threadpool threads with no running loop). Schedules the puts onto the
        main loop via ``call_soon_threadsafe``.
        """
        subscribers = self._subscribers.get(session_id)
        if not subscribers:
            return  # No subscribers for this session — nothing to do.
        loop = self._loop
        if loop is None:
            logger.warning("publish() called before loop captured; event dropped: %s %s", event_type, data)
            return
        payload = {"type": event_type, "data": data}
        # Snapshot to a list: publish() runs on a threadpool thread while
        # unsubscribe() (on the event loop) can discard from / delete the same
        # set concurrently. Iterating the live set across that mutation raises
        # `RuntimeError: Set changed size during iteration`. The snapshot is a
        # cheap copy of the (typically small) subscriber set.
        for queue in list(subscribers):
            # call_soon_threadsafe is safe from any thread, including the
            # threadpool threads that run sync route handlers. _safe_put applies
            # drop-oldest backpressure if the subscriber's bounded queue is full.
            loop.call_soon_threadsafe(_safe_put, queue, payload)


# Single shared instance (module-level). All routes and the stream endpoint
# use this one bus.
event_bus = EventBus()
