def test_submit_idea(client, sample_session):
    session_id = sample_session["id"]
    client.post(f"/sessions/{session_id}/join?name=Anna")

    response = client.post(
        f"/sessions/{session_id}/ideas",
        json={
            "participant_id": "p1",
            "participant_name": "Anna",
            "content": "Better onboarding docs",
            "category": "strength",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Better onboarding docs"
    assert data["category"] == "strength"
    assert data["participant_name"] == "Anna"
    assert data["session_id"] == session_id
    assert data["votes"] == 0


def test_submit_idea_without_category(client, sample_session):
    session_id = sample_session["id"]
    response = client.post(
        f"/sessions/{session_id}/ideas",
        json={
            "participant_id": "p1",
            "participant_name": "Anna",
            "content": "Some idea",
        },
    )
    assert response.status_code == 200
    assert response.json()["category"] is None


def test_submit_idea_empty_content(client, sample_session):
    session_id = sample_session["id"]
    response = client.post(
        f"/sessions/{session_id}/ideas",
        json={
            "participant_id": "p1",
            "participant_name": "Anna",
            "content": "",
        },
    )
    assert response.status_code == 422


def test_submit_idea_session_not_found(client):
    response = client.post(
        "/sessions/doesnotexist/ideas",
        json={
            "participant_id": "p1",
            "participant_name": "Anna",
            "content": "Idea",
        },
    )
    assert response.status_code == 404


def test_list_ideas(client, sample_session):
    session_id = sample_session["id"]
    client.post(
        f"/sessions/{session_id}/ideas",
        json={"participant_id": "p1", "participant_name": "Anna", "content": "Idea 1"},
    )
    client.post(
        f"/sessions/{session_id}/ideas",
        json={"participant_id": "p2", "participant_name": "Mohand", "content": "Idea 2"},
    )

    response = client.get(f"/sessions/{session_id}/ideas")
    assert response.status_code == 200
    ideas = response.json()
    assert len(ideas) == 2
    contents = [i["content"] for i in ideas]
    assert "Idea 1" in contents
    assert "Idea 2" in contents


def test_list_ideas_empty(client, sample_session):
    response = client.get(f"/sessions/{sample_session['id']}/ideas")
    assert response.status_code == 200
    assert response.json() == []


def test_list_ideas_session_not_found(client):
    response = client.get("/sessions/doesnotexist/ideas")
    assert response.status_code == 404


# ── Voting ────────────────────────────────────────────────────


def _submit_one_idea(client, session_id, content="An idea") -> dict:
    resp = client.post(
        f"/sessions/{session_id}/ideas",
        json={"participant_id": "p1", "participant_name": "Anna", "content": content},
    )
    assert resp.status_code == 200
    return resp.json()


def test_vote_increments_count(client, sample_session):
    session_id = sample_session["id"]
    idea = _submit_one_idea(client, session_id)
    assert idea["votes"] == 0

    r1 = client.post(f"/sessions/{session_id}/ideas/{idea['id']}/vote")
    assert r1.status_code == 200
    assert r1.json()["votes"] == 1

    r2 = client.post(f"/sessions/{session_id}/ideas/{idea['id']}/vote")
    assert r2.json()["votes"] == 2


def test_vote_idea_not_found(client, sample_session):
    session_id = sample_session["id"]
    r = client.post(f"/sessions/{session_id}/ideas/doesnotexist/vote")
    assert r.status_code == 404


def test_vote_session_not_found(client):
    r = client.post("/sessions/doesnotexist/ideas/whatever/vote")
    assert r.status_code == 404
