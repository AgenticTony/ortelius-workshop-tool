"""Unit tests for the Postgres LISTEN/NOTIFY event bus.

The LISTEN loop needs a live Postgres (not available in the SQLite CI suite);
these tests cover the pure, DB-free parts: payload dispatch to local queues,
malformed-payload handling, and the config-driven factory selection.
"""
import asyncio
import json

import pytest

from app.dependencies import get_event_bus
from app.services.event_bus import EventBus
from app.services.pg_event_bus import PostgresListenNotifyEventBus


@pytest.mark.asyncio
async def test_dispatch_fans_out_to_local_queue():
    bus = PostgresListenNotifyEventBus("postgresql://unused")
    bus._loop = asyncio.get_running_loop()
    queue = await bus.subscribe("s1")
    try:
        bus._dispatch(
            json.dumps({"session_id": "s1", "type": "idea_added", "data": {"id": "x"}})
        )
        # call_soon_threadsafe schedules on the loop; yield so it lands.
        await asyncio.sleep(0.05)
        payload = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert payload == {"type": "idea_added", "data": {"id": "x"}}
    finally:
        await bus.unsubscribe("s1", queue)


def test_dispatch_drops_malformed_payload():
    bus = PostgresListenNotifyEventBus("postgresql://unused")
    bus._dispatch("not-json")  # must not raise
    bus._dispatch(json.dumps({"no_session": True}))  # missing session_id: no-op


def test_dispatch_without_loop_is_noop():
    bus = PostgresListenNotifyEventBus("postgresql://unused")
    bus._loop = None
    bus._dispatch(json.dumps({"session_id": "s1", "type": "x", "data": {}}))  # no crash


def test_factory_defaults_to_in_memory(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "event_bus_backend", "memory")
    assert isinstance(get_event_bus(), EventBus)


def test_factory_selects_postgres_when_configured(monkeypatch):
    import app.dependencies as deps
    from app.config import settings

    monkeypatch.setattr(settings, "event_bus_backend", "postgres")
    monkeypatch.setattr(settings, "database_url", "postgresql://configured")
    monkeypatch.setattr(deps, "_pg_bus", None)
    bus = get_event_bus()
    try:
        assert isinstance(bus, PostgresListenNotifyEventBus)
    finally:
        # Don't leak the constructed bus into other tests.
        monkeypatch.setattr(deps, "_pg_bus", None)


def test_pg_publish_reuses_one_connection(monkeypatch):
    """publish() reuses a single persistent connection across calls (and proves
    the method/attribute accessors don't collide — an earlier version named the
    connection getter the same as the connection attribute, shadowing the method
    and making every publish TypeError). No real Postgres needed.
    """
    import psycopg2

    connects: list[str] = []
    notified: list[tuple[str, object]] = []

    class _Cursor:
        def __init__(self, conn: "_Conn") -> None:
            self._conn = conn

        def __enter__(self) -> "_Cursor":
            return self

        def __exit__(self, *exc: object) -> None:
            pass

        def execute(self, sql: str, params: object = None) -> None:
            notified.append((sql, params))

    class _Conn:
        def __init__(self) -> None:
            self.closed = False

        def set_isolation_level(self, _level: int) -> None:
            pass

        def cursor(self) -> _Cursor:
            return _Cursor(self)

        def close(self) -> None:
            self.closed = True

    def fake_connect(url: str, connect_timeout: int = 5) -> _Conn:
        connects.append(url)
        return _Conn()

    monkeypatch.setattr(psycopg2, "connect", fake_connect)

    bus = PostgresListenNotifyEventBus("postgresql://x")
    bus.publish("s1", "idea_added", {"id": "i1"})
    bus.publish("s1", "idea_voted", {"id": "i1"})

    assert len(connects) == 1  # connection reused, not one-per-publish
    assert all(call[0] == "SELECT pg_notify(%s, %s);" for call in notified)
