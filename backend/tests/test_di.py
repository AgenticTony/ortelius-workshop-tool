"""Dependency-injection seams: routes depend on abstractions, not singletons."""
from app.dependencies import get_event_bus
from app.services.event_bus import EventBusProtocol


class _RecordingBus:
    """A minimal EventBusProtocol stand-in that records publish() calls."""

    events: list[tuple[str, str, object]]

    def __init__(self) -> None:
        self.events = []

    def set_loop(self, loop) -> None:  # noqa: ANN001 - matches Protocol shape
        pass

    async def subscribe(self, session_id: str):  # noqa: ANN201
        raise AssertionError("not used in this test")

    async def unsubscribe(self, session_id: str, queue) -> None:  # noqa: ANN001
        pass

    def publish(self, session_id: str, event_type: str, data: object) -> None:
        self.events.append((session_id, event_type, data))


def test_event_bus_is_overridable_via_di(client, sample_session):
    """Overriding get_event_bus swaps the bus the routes publish through.

    This is the multi-worker readiness seam: a Redis/LISTEN-NOTIFY bus can be
    injected here without touching route code.
    """
    rec = _RecordingBus()
    assert isinstance(rec, EventBusProtocol)  # structural typing: satisfies the Protocol

    client.app.dependency_overrides[get_event_bus] = lambda: rec
    try:
        client.post(f"/sessions/{sample_session['id']}/join", json={"name": "Anna"})
    finally:
        client.app.dependency_overrides.pop(get_event_bus, None)

    # The route published participant_joined through OUR overridden bus, not the
    # real singleton — proving routes depend on the Protocol via DI.
    assert any(et == "participant_joined" for _, et, _ in rec.events)
