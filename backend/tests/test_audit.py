"""Audit logging: state-changing routes emit structured lines to the audit logger."""
import logging


def test_session_create_is_audited(client, caplog):
    with caplog.at_level(logging.INFO, logger="audit"):
        response = client.post("/sessions", json={"topic": "Audit", "framework": "swot"})
    assert response.status_code == 200
    session_id = response.json()["id"]
    messages = [r.getMessage() for r in caplog.records if r.name == "audit"]
    assert any("action=session_created" in m and f"session={session_id}" in m for m in messages)


def test_join_and_idea_submit_are_audited(client, sample_session, participant_headers, caplog):
    session_id = sample_session["id"]
    with caplog.at_level(logging.INFO, logger="audit"):
        client.post(f"/sessions/{session_id}/join", json={"name": "Anna"})
        client.post(
            f"/sessions/{session_id}/ideas",
            headers=participant_headers,
            json={"participant_id": "p1", "participant_name": "Anna", "content": "X"},
        )
    actions = [r.getMessage() for r in caplog.records if r.name == "audit"]
    assert any("action=participant_joined" in a for a in actions)
    assert any("action=idea_submitted" in a for a in actions)
