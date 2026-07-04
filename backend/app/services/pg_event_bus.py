"""Postgres LISTEN/NOTIFY-backed event bus for multi-worker SSE fan-out.

The in-memory [EventBus] only reaches subscribers in its own process, so it
caps the deployment to a single uvicorn worker. This implementation uses
Postgres ``LISTEN``/``NOTIFY`` (available on the existing Supabase/Postgres —
no extra broker to stand up) so a notification published by any worker is
delivered to every worker's local subscriber queues.

Architecture:
- One process-wide ``LISTEN`` connection in a daemon thread drains notifications
  and fans them out to local in-process subscriber queues (same bounded-queue +
  drop-oldest backpressure as the in-memory bus).
- ``publish`` issues ``pg_notify(channel, payload)`` on a short-lived
  connection (thread-safe by construction; each thread its own connection).

This is exercised in production; the SQLite test suite can't run LISTEN/NOTIFY,
so the unit test covers the pure payload/dispatch logic with a stub. Validate
end-to-end against a real Postgres during the deploy verification step.
"""
from __future__ import annotations

import asyncio
import json
import logging
import select
import threading
from collections import defaultdict
from typing import Any

from app.metrics import SSE_SUBSCRIBERS
from app.services.event_bus import MAX_SUBSCRIBER_QUEUE, _safe_put

logger = logging.getLogger(__name__)


class PostgresListenNotifyEventBus:
    """[EventBusProtocol] backed by Postgres LISTEN/NOTIFY."""

    CHANNEL = "workshop_events"

    def __init__(self, database_url: str, max_queue: int = MAX_SUBSCRIBER_QUEUE) -> None:
        self._database_url = database_url
        self._max_queue = max_queue
        self._subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._listen_thread: threading.Thread | None = None
        self._publish_lock = threading.Lock()
        self._publish_conn: Any = None

    # ── Protocol surface ───────────────────────────────────────
    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        # Store the loop and start the LISTEN thread WITHOUT blocking it —
        # the blocking connect+LISTEN happens inside the thread, so the async
        # lifespan (which calls this) never stalls on a DB handshake.
        self._loop = loop
        if self._listen_thread and self._listen_thread.is_alive():
            return
        self._listen_thread = threading.Thread(
            target=self._listener_main, name="pg-event-listen", daemon=True
        )
        self._listen_thread.start()

    async def subscribe(self, session_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=self._max_queue)
        self._subscribers[session_id].add(queue)
        SSE_SUBSCRIBERS.inc()
        logger.debug("PG SSE subscriber added for %s", session_id)
        return queue

    async def unsubscribe(self, session_id: str, queue: asyncio.Queue) -> None:
        subscribers = self._subscribers.get(session_id)
        existed = subscribers is not None and queue in subscribers
        if subscribers is not None:
            subscribers.discard(queue)
        if not self._subscribers.get(session_id):
            self._subscribers.pop(session_id, None)
        if existed:
            SSE_SUBSCRIBERS.dec()

    def publish(self, session_id: str, event_type: str, data: Any) -> None:
        payload = json.dumps(
            {"session_id": session_id, "type": event_type, "data": data}, default=str
        )
        # NOTIFY rejects payloads >8000 bytes (it does NOT truncate). Our
        # payloads (idea content ≤2000 chars + metadata) stay well under, but
        # guard so a future large payload fails loudly here rather than 500-ing
        # the route after the DB write already committed.
        if len(payload) > 8000:
            logger.error("NOTIFY payload >8000 bytes for %s; dropping event", event_type)
            return
        # Reuse a single autocommit connection across publishes (guarded by a
        # lock — psycopg2 connections aren't thread-safe); reconnect if it died.
        with self._publish_lock:
            conn = self._get_publish_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT pg_notify(%s, %s);", (self.CHANNEL, payload))
            except Exception:
                self._close_publish_conn()
                raise

    # ── Connections ────────────────────────────────────────────
    def _connect(self) -> Any:
        import psycopg2  # noqa: PLC0415

        return psycopg2.connect(self._database_url, connect_timeout=5)

    def _get_publish_conn(self) -> Any:
        import psycopg2  # noqa: PLC0415

        if self._publish_conn is None or self._publish_conn.closed:
            self._publish_conn = self._connect()
            self._publish_conn.set_isolation_level(
                psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
            )
        return self._publish_conn

    def _close_publish_conn(self) -> None:
        if self._publish_conn is not None:
            try:
                self._publish_conn.close()
            except Exception:  # noqa: BLE001
                pass
        self._publish_conn = None

    # ── LISTEN thread (self-healing) ───────────────────────────
    def _listener_main(self) -> None:  # pragma: no cover - needs a live Postgres
        """(Re)connect, LISTEN, and drain until the connection dies; repeat.

        On any error (server restart, idle kill, network blip) the connection
        is closed and re-established so NOTIFY delivery resumes — it never
        spins on a dead socket.
        """
        import time  # noqa: PLC0415

        import psycopg2  # noqa: PLC0415

        while True:
            conn = None
            try:
                conn = self._connect()
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                with conn.cursor() as cur:
                    cur.execute(f"LISTEN {self.CHANNEL};")
                logger.info("Postgres LISTEN connected on channel %s", self.CHANNEL)
                self._drain(conn)
            except Exception:  # noqa: BLE001 - reconnect on ANY connection failure
                logger.exception("Postgres LISTEN connection lost; reconnecting in 2s")
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:  # noqa: BLE001
                        pass
                time.sleep(2)

    def _drain(self, conn: Any) -> None:  # pragma: no cover - needs a live Postgres
        """Block on the LISTEN connection until it fails, dispatching notifies."""
        while True:
            select.select([conn], [], [], 1.0)
            conn.poll()
            while conn.notifies:
                self._dispatch(conn.notifies.pop(0).payload)

    def _dispatch(self, payload_json: str) -> None:
        """Fan a received notification out to local subscriber queues.

        Pure (no DB) so it's unit-testable without Postgres.
        """
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            logger.warning("Dropping malformed NOTIFY payload: %r", payload_json[:200])
            return
        session_id = payload.get("session_id")
        loop = self._loop
        if not session_id or loop is None:
            return
        subscribers = self._subscribers.get(session_id)
        if not subscribers:
            return
        event = {"type": payload.get("type"), "data": payload.get("data")}
        # Snapshot (list) — subscribe/unsubscribe on the loop can mutate the set.
        for queue in list(subscribers):
            loop.call_soon_threadsafe(_safe_put, queue, event)

