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


# ── Voting (dot-voting: one per idea, budget of 3, toggle off via DELETE) ──


def _submit_one_idea(client, session_id, headers, content="An idea") -> dict:
    resp = client.post(
        f"/sessions/{session_id}/ideas",
        headers=headers,
        json={"participant_id": "p1", "participant_name": "Anna", "content": content},
    )
    assert resp.status_code == 200
    return resp.json()


def test_vote_increments_count(client, sample_session, participant_headers):
    """Voting once bumps the count to 1 and marks voted_by_me=True."""
    session_id = sample_session["id"]
    idea = _submit_one_idea(client, session_id, participant_headers)
    assert idea["votes"] == 0

    r = client.post(
        f"/sessions/{session_id}/ideas/{idea['id']}/vote", headers=participant_headers
    )
    assert r.status_code == 200
    body = r.json()
    assert body["votes"] == 1
    assert body["voted_by_me"] is True


def test_vote_twice_same_idea_rejected(client, sample_session, participant_headers):
    """Dot-voting: a participant can't vote on the same idea twice."""
    session_id = sample_session["id"]
    idea = _submit_one_idea(client, session_id, participant_headers)

    r1 = client.post(
        f"/sessions/{session_id}/ideas/{idea['id']}/vote", headers=participant_headers
    )
    assert r1.status_code == 200

    r2 = client.post(
        f"/sessions/{session_id}/ideas/{idea['id']}/vote", headers=participant_headers
    )
    assert r2.status_code == 409
    assert r2.json()["code"] == "already_voted"


def test_vote_budget_exhausted(client, sample_session, participant_headers):
    """With a budget of 3, the 4th distinct-idea vote is rejected."""
    session_id = sample_session["id"]
    idea_ids = [
        _submit_one_idea(client, session_id, participant_headers, content=f"Idea {n}")["id"]
        for n in range(4)
    ]
    # Cast the 3 allowed votes.
    for iid in idea_ids[:3]:
        r = client.post(
            f"/sessions/{session_id}/ideas/{iid}/vote", headers=participant_headers
        )
        assert r.status_code == 200

    # The 4th should be rejected (budget exhausted).
    r = client.post(
        f"/sessions/{session_id}/ideas/{idea_ids[3]}/vote", headers=participant_headers
    )
    assert r.status_code == 409
    assert r.json()["code"] == "vote_budget_exceeded"


def test_unvote_decrements_and_restores_budget(client, sample_session, participant_headers):
    """DELETE /vote removes the vote, decrements the count, frees budget."""
    session_id = sample_session["id"]
    idea = _submit_one_idea(client, session_id, participant_headers)
    client.post(
        f"/sessions/{session_id}/ideas/{idea['id']}/vote", headers=participant_headers
    )

    r = client.delete(
        f"/sessions/{session_id}/ideas/{idea['id']}/vote", headers=participant_headers
    )
    assert r.status_code == 200
    body = r.json()
    assert body["votes"] == 0
    assert body["voted_by_me"] is False

    # Budget restored — can vote again.
    r2 = client.post(
        f"/sessions/{session_id}/ideas/{idea['id']}/vote", headers=participant_headers
    )
    assert r2.status_code == 200
    assert r2.json()["votes"] == 1


def test_unvote_when_not_voted(client, sample_session, participant_headers):
    """Un-voting an idea you never voted on is 404."""
    session_id = sample_session["id"]
    idea = _submit_one_idea(client, session_id, participant_headers)
    r = client.delete(
        f"/sessions/{session_id}/ideas/{idea['id']}/vote", headers=participant_headers
    )
    assert r.status_code == 404
    assert r.json()["code"] == "not_voted"


def test_vote_counts_are_independent_per_participant(
    client, sample_session, participant_headers, second_participant_headers
):
    """Two participants each voting the same idea → count is 2."""
    session_id = sample_session["id"]
    idea = _submit_one_idea(client, session_id, participant_headers)

    r1 = client.post(
        f"/sessions/{session_id}/ideas/{idea['id']}/vote", headers=participant_headers
    )
    assert r1.status_code == 200
    assert r1.json()["votes"] == 1

    r2 = client.post(
        f"/sessions/{session_id}/ideas/{idea['id']}/vote", headers=second_participant_headers
    )
    assert r2.status_code == 200
    assert r2.json()["votes"] == 2


def test_voted_by_me_in_list(client, sample_session, participant_headers, second_participant_headers):
    """The list endpoint reports voted_by_me per the calling participant."""
    session_id = sample_session["id"]
    idea = _submit_one_idea(client, session_id, participant_headers)
    client.post(
        f"/sessions/{session_id}/ideas/{idea['id']}/vote", headers=participant_headers
    )

    # Voter sees voted_by_me=True.
    voter_list = client.get(
        f"/sessions/{session_id}/ideas", headers=participant_headers
    ).json()
    assert voter_list[0]["voted_by_me"] is True

    # The other participant sees voted_by_me=False.
    other_list = client.get(
        f"/sessions/{session_id}/ideas", headers=second_participant_headers
    ).json()
    assert other_list[0]["voted_by_me"] is False


def test_facilitator_cannot_vote(client, sample_session, auth_headers):
    """Facilitators are not participants — voting is 403."""
    session_id = sample_session["id"]
    # Facilitator seeds an idea (allowed).
    idea = client.post(
        f"/sessions/{session_id}/ideas",
        headers=auth_headers(sample_session),
        json={"participant_id": "fac", "participant_name": "Facilitator", "content": "Seeded"},
    ).json()
    r = client.post(
        f"/sessions/{session_id}/ideas/{idea['id']}/vote", headers=auth_headers(sample_session)
    )
    assert r.status_code == 403
    assert r.json()["code"] == "forbidden"


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
