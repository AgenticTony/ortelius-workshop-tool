"""Tests for the typed-error layer and global exception handlers.

Verifies:
- Claude outages surface as 503 claude_error (not an opaque 500).
- Unparseable-after-retry responses surface as 502 claude_parse_error.
- Unknown framework on the analysis path surfaces as 422 (was an uncaught 500).
- Unhandled exceptions return a clean 500 with no stack trace leak + a
  request_id, via the global handler.
- Typed errors carry the consistent {detail, code} shape.
"""
from unittest.mock import patch

import anthropic

from app.errors import (
    ClaudeAPIError,
    ClaudeParseError,
    FrameworkNotFoundError,
    SessionNotFoundError,
    WorkshopError,
)
from app.main import app

# ── Unit: error classes ──────────────────────────────────────


def test_typed_error_carries_status_code_and_code():
    err = SessionNotFoundError("abc")
    assert err.status_code == 404
    assert err.code == "session_not_found"
    assert err.detail == "Session not found"


def test_workshop_error_default_status_is_500():
    err = WorkshopError("boom")
    assert err.status_code == 500
    assert err.code == "workshop_error"


# ── Integration: error → HTTP response shape ─────────────────


def test_session_not_found_returns_typed_body(client):
    r = client.get("/sessions/doesnotexist")
    assert r.status_code == 404
    body = r.json()
    assert body["detail"] == "Session not found"
    assert body["code"] == "session_not_found"


def test_invalid_access_code_returns_typed_body(client):
    r = client.post(
        "/sessions/join/NOPE",
        json={"name": "Anna"},
    )
    assert r.status_code == 404
    assert r.json()["code"] == "invalid_access_code"


def test_auth_error_includes_www_authenticate_header(client, sample_session):
    # analyse without a token -> 401 with WWW-Authenticate: Bearer
    r = client.post(f"/sessions/{sample_session['id']}/analyse")
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"
    assert r.json()["code"] == "unauthorized"


# ── Claude outage / parse failure (mocked) ───────────────────


def _seed_idea(client, session_id):
    r = client.post(
        f"/sessions/{session_id}/ideas",
        json={"participant_id": "p1", "participant_name": "Anna", "content": "An idea"},
    )
    assert r.status_code == 200


def test_claude_outage_returns_503(client, sample_session, auth_headers):
    session_id = sample_session["id"]
    _seed_idea(client, session_id)

    def _raise(*args, **kwargs):
        raise anthropic.APIConnectionError(request=None)  # type: ignore[arg-type]

    with patch("app.routes.analysis.analyse_ideas", side_effect=ClaudeAPIError()):
        r = client.post(
            f"/sessions/{session_id}/analyse",
            headers=auth_headers(sample_session),
        )
    assert r.status_code == 503
    assert r.json()["code"] == "claude_error"


def test_claude_parse_error_returns_502(client, sample_session, auth_headers):
    session_id = sample_session["id"]
    _seed_idea(client, session_id)

    with patch("app.routes.analysis.analyse_ideas", side_effect=ClaudeParseError()):
        r = client.post(
            f"/sessions/{session_id}/analyse",
            headers=auth_headers(sample_session),
        )
    assert r.status_code == 502
    assert r.json()["code"] == "claude_parse_error"


def test_unknown_framework_on_analysis_returns_422(client, sample_session, auth_headers):
    """A session whose framework id isn't in the registry should 422, not 500.

    We simulate by patching analyse_ideas to raise FrameworkNotFoundError
    (which the real claude_service now does via _resolve_config).
    """
    session_id = sample_session["id"]
    _seed_idea(client, session_id)

    with patch(
        "app.routes.analysis.analyse_ideas",
        side_effect=FrameworkNotFoundError("bogus"),
    ):
        r = client.post(
            f"/sessions/{session_id}/analyse",
            headers=auth_headers(sample_session),
        )
    assert r.status_code == 422
    assert r.json()["code"] == "framework_not_found"


# ── Global catch-all handler ─────────────────────────────────


def test_unhandled_exception_returns_clean_500(
    client, sample_session, auth_headers
):
    session_id = sample_session["id"]
    _seed_idea(client, session_id)

    # TestClient re-raises server exceptions by default, preventing the global
    # handler from returning its clean 500. Disable that for this test so we
    # exercise the real handler path.
    from fastapi.testclient import TestClient
    no_raise_client = TestClient(app, raise_server_exceptions=False)

    with patch(
        "app.routes.analysis.analyse_ideas",
        side_effect=RuntimeError("boom"),
    ):
        r = no_raise_client.post(
            f"/sessions/{session_id}/analyse",
            headers=auth_headers(sample_session),
        )
    assert r.status_code == 500
    body = r.json()
    assert body["detail"] == "Internal server error"
    assert body["code"] == "internal_error"
    assert "request_id" in body
    # The internal error message must NOT leak to the client.
    assert "boom" not in r.text


def test_request_id_header_returned(client):
    r = client.get("/health")
    assert "x-request-id" in {k.lower() for k in r.headers.keys()}


def test_client_request_id_is_echoed(client):
    r = client.get("/health", headers={"X-Request-ID": "abc-123"})
    assert r.headers["x-request-id"] == "abc-123"
