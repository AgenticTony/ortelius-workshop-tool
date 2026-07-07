def test_submit_idea(client, sample_session, participant_headers):
    session_id = sample_session["id"]

    response = client.post(
        f"/sessions/{session_id}/ideas",
        headers=participant_headers,
        json={
            "participant_id": "p1",  # ignored: author is the authenticated participant
            "participant_name": "Ignored",
            "content": "Better onboarding docs",
            "category": "strength",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Better onboarding docs"
    assert data["category"] == "strength"
    assert data["participant_name"] == "Anna"  # from the authenticated participant row
    assert data["session_id"] == session_id
    assert data["votes"] == 0


def test_submit_idea_without_category(client, sample_session, participant_headers):
    session_id = sample_session["id"]
    response = client.post(
        f"/sessions/{session_id}/ideas",
        headers=participant_headers,
        json={
            "participant_id": "p1",
            "participant_name": "Anna",
            "content": "Some idea",
        },
    )
    assert response.status_code == 200
    assert response.json()["category"] is None


def test_submit_idea_empty_content(client, sample_session, participant_headers):
    session_id = sample_session["id"]
    response = client.post(
        f"/sessions/{session_id}/ideas",
        headers=participant_headers,
        json={
            "participant_id": "p1",
            "participant_name": "Anna",
            "content": "",
        },
    )
    assert response.status_code == 422


def test_submit_idea_session_not_found(client, participant_headers):
    # Authenticated, but the session doesn't exist → 404 (not 401).
    response = client.post(
        "/sessions/doesnotexist/ideas",
        headers=participant_headers,
        json={
            "participant_id": "p1",
            "participant_name": "Anna",
            "content": "Idea",
        },
    )
    assert response.status_code == 404


def test_submit_idea_unauthenticated_rejected(client, sample_session):
    # No Authorization header → 401 (and the session existence is not leaked).
    response = client.post(
        f"/sessions/{sample_session['id']}/ideas",
        json={"participant_id": "p1", "participant_name": "Anna", "content": "X"},
    )
    assert response.status_code == 401


def test_list_ideas(client, sample_session, participant_headers):
    session_id = sample_session["id"]
    client.post(
        f"/sessions/{session_id}/ideas",
        headers=participant_headers,
        json={"participant_id": "p1", "participant_name": "Anna", "content": "Idea 1"},
    )
    client.post(
        f"/sessions/{session_id}/ideas",
        headers=participant_headers,
        json={"participant_id": "p2", "participant_name": "Mohand", "content": "Idea 2"},
    )

    response = client.get(f"/sessions/{session_id}/ideas", headers=participant_headers)
    assert response.status_code == 200
    ideas = response.json()
    assert len(ideas) == 2
    contents = [i["content"] for i in ideas]
    assert "Idea 1" in contents
    assert "Idea 2" in contents


def test_list_ideas_empty(client, sample_session, participant_headers):
    response = client.get(
        f"/sessions/{sample_session['id']}/ideas", headers=participant_headers
    )
    assert response.status_code == 200
    assert response.json() == []


def test_list_ideas_session_not_found(client, participant_headers):
    response = client.get("/sessions/doesnotexist/ideas", headers=participant_headers)
    assert response.status_code == 404


# ── Voting ────────────────────────────────────────────────────


def _submit_one_idea(client, session_id, headers, content="An idea") -> dict:
    resp = client.post(
        f"/sessions/{session_id}/ideas",
        headers=headers,
        json={"participant_id": "p1", "participant_name": "Anna", "content": content},
    )
    assert resp.status_code == 200
    return resp.json()


def test_vote_increments_count(client, sample_session, participant_headers):
    session_id = sample_session["id"]
    idea = _submit_one_idea(client, session_id, participant_headers)
    assert idea["votes"] == 0

    r1 = client.post(
        f"/sessions/{session_id}/ideas/{idea['id']}/vote", headers=participant_headers
    )
    assert r1.status_code == 200
    assert r1.json()["votes"] == 1

    r2 = client.post(
        f"/sessions/{session_id}/ideas/{idea['id']}/vote", headers=participant_headers
    )
    assert r2.json()["votes"] == 2


def test_vote_idea_not_found(client, sample_session, participant_headers):
    session_id = sample_session["id"]
    r = client.post(
        f"/sessions/{session_id}/ideas/doesnotexist/vote", headers=participant_headers
    )
    assert r.status_code == 404


def test_vote_session_not_found(client, participant_headers):
    r = client.post(
        "/sessions/doesnotexist/ideas/whatever/vote", headers=participant_headers
    )
    assert r.status_code == 404
