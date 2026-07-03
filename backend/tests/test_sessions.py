def test_create_session(client):
    response = client.post(
        "/sessions",
        json={"topic": "Improve onboarding", "framework": "swot"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "Improve onboarding"
    assert data["framework"] == "swot"
    assert data["status"] == "active"
    assert len(data["access_code"]) == 6
    assert data["id"]
    assert data["participants"] == []


def test_create_session_default_framework(client):
    response = client.post(
        "/sessions",
        json={"topic": "Test", "framework": "pestel"},
    )
    assert response.status_code == 200
    assert response.json()["framework"] == "pestel"


def test_create_two_sessions_unique_codes(client):
    r1 = client.post("/sessions", json={"topic": "A", "framework": "swot"})
    r2 = client.post("/sessions", json={"topic": "B", "framework": "swot"})
    assert r1.json()["access_code"] != r2.json()["access_code"]


def test_get_session(client, sample_session):
    response = client.get(f"/sessions/{sample_session['id']}")
    assert response.status_code == 200
    assert response.json()["topic"] == "Test Workshop"


def test_get_session_not_found(client):
    response = client.get("/sessions/doesnotexist")
    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


def test_join_session(client, sample_session):
    response = client.post(f"/sessions/{sample_session['id']}/join?name=Anna")
    assert response.status_code == 200
    data = response.json()
    assert "participant_id" in data
    assert len(data) == 1


def test_join_session_empty_name(client, sample_session):
    response = client.post(f"/sessions/{sample_session['id']}/join?name=")
    assert response.status_code == 422


def test_join_session_whitespace_name(client, sample_session):
    response = client.post(f"/sessions/{sample_session['id']}/join?name=%20%20")
    assert response.status_code == 422


def test_join_session_not_found(client):
    response = client.post("/sessions/doesnotexist/join?name=Anna")
    assert response.status_code == 404


def test_join_by_access_code(client, sample_session):
    code = sample_session["access_code"]
    response = client.post(
        f"/sessions/join/{code}",
        json={"name": "Mohand"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "participant_id" in data


def test_join_by_access_code_invalid(client):
    response = client.post(
        "/sessions/join/INVALID",
        json={"name": "Test"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Invalid access code"


def test_join_by_code_validates_name(client, sample_session):
    code = sample_session["access_code"]
    response = client.post(f"/sessions/join/{code}", json={"name": ""})
    assert response.status_code == 422


def test_get_session_shows_participants(client, sample_session):
    client.post(f"/sessions/{sample_session['id']}/join?name=Anna")
    client.post(f"/sessions/{sample_session['id']}/join?name=Mohand")
    response = client.get(f"/sessions/{sample_session['id']}")
    assert response.status_code == 200
    participants = response.json()["participants"]
    assert len(participants) == 2
    names = [p["name"] for p in participants]
    assert "Anna" in names
    assert "Mohand" in names
