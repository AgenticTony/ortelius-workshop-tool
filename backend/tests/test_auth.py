"""Participant/facilitator auth on the participant-scoped routes."""
from app.dependencies import resolve_principal
from app.errors import AuthenticationError
from app.models.db_models import ParticipantDB
from app.security import generate_token


def test_facilitator_token_authorizes_participant_routes(client, sample_session, auth_headers):
    """The facilitator token is accepted on submit/vote/list (facilitator can seed/act)."""
    session_id = sample_session["id"]
    r = client.post(
        f"/sessions/{session_id}/ideas",
        headers=auth_headers(sample_session),
        json={"participant_id": "fac", "participant_name": "Facilitator", "content": "seed"},
    )
    assert r.status_code == 200
    assert r.json()["participant_name"] == "Facilitator"


def test_participant_token_does_not_cross_sessions(client, sample_session, participant_headers):
    """A participant token for one session is rejected on another (→ 401)."""
    other = client.post("/sessions", json={"topic": "Other", "framework": "swot"}).json()
    r = client.get(f"/sessions/{other['id']}/ideas", headers=participant_headers)
    assert r.status_code == 401


def test_resolve_principal_participant_then_facilitator(client, sample_session):
    """resolve_principal returns a participant principal for a participant token,
    and a facilitator principal for the facilitator token."""
    from app.dependencies import get_db

    session_id = sample_session["id"]
    join = client.post(f"/sessions/{session_id}/join", json={"name": "Anna"}).json()
    db = next(client.app.dependency_overrides[get_db]())
    try:
        p = resolve_principal(session_id, join["participant_token"], db)
        assert p.role == "participant"
        assert p.participant_id == join["participant_id"]

        f = resolve_principal(session_id, sample_session["facilitator_token"], db)
        assert f.role == "facilitator"
        assert f.participant_id is None
    finally:
        db.close()


def test_resolve_principal_rejects_unknown_token(client, sample_session):
    from app.dependencies import get_db

    db = next(client.app.dependency_overrides[get_db]())
    try:
        import pytest
        with pytest.raises(AuthenticationError):
            resolve_principal(sample_session["id"], generate_token(), db)
    finally:
        db.close()


def test_pre_auth_participants_still_resolve_via_facilitator(client, sample_session, auth_headers):
    """A participant row with no token_hash (pre-auth migration) can't authenticate
    as itself, but the facilitator token still governs the session."""
    from app.dependencies import get_db

    session_id = sample_session["id"]
    db = next(client.app.dependency_overrides[get_db]())
    try:
        db.add(ParticipantDB(session_id=session_id, name="Legacy", token_hash=None))
        db.commit()
    finally:
        db.close()

    # No participant token was issued for the legacy row; only the facilitator
    # can act on the session until that participant re-joins.
    r = client.get(f"/sessions/{session_id}/ideas", headers=auth_headers(sample_session))
    assert r.status_code == 200
