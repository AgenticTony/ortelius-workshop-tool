from unittest.mock import patch

from app.models import AnalysisResult
from app.models.db_models import AnalysisDB


MOCK_ANALYSIS = AnalysisResult(
    session_id="mock",
    framework="swot",
    categories={
        "strengths": [{"idea_id": "i1", "summary": "Good team"}],
        "weaknesses": [],
        "opportunities": [{"idea_id": "i2", "summary": "New market"}],
        "threats": [],
    },
    key_themes=["Teamwork", "Growth"],
    decisions_made=["Launch Q3"],
    open_questions=["Budget?"],
    recommended_next_steps=["Draft plan"],
)


def test_get_analysis_not_run(client, sample_session_with_participant):
    session_id = sample_session_with_participant["id"]
    response = client.get(f"/sessions/{session_id}/analysis")
    assert response.status_code == 404
    assert "POST /analyse first" in response.json()["detail"]


def test_get_analysis_session_not_found(client):
    response = client.get("/sessions/doesnotexist/analysis")
    assert response.status_code == 404


def test_run_analysis_no_ideas(client, sample_session):
    response = client.post(f"/sessions/{sample_session['id']}/analyse")
    assert response.status_code == 400
    assert "No ideas to analyse" in response.json()["detail"]


def test_run_analysis_session_not_found(client):
    response = client.post("/sessions/doesnotexist/analyse")
    assert response.status_code == 404


@patch("app.routes.analysis.analyse_ideas", return_value=MOCK_ANALYSIS)
def test_run_analysis_success(mock_claude, client, sample_session):
    session_id = sample_session["id"]
    client.post(
        f"/sessions/{session_id}/ideas",
        json={"participant_id": "p1", "participant_name": "Anna", "content": "Good team"},
    )

    response = client.post(f"/sessions/{session_id}/analyse")
    assert response.status_code == 200
    data = response.json()
    assert data["framework"] == "swot"
    assert len(data["key_themes"]) == 2
    assert "Teamwork" in data["key_themes"]
    assert data["categories"]["strengths"][0]["summary"] == "Good team"


@patch("app.routes.analysis.analyse_ideas", return_value=MOCK_ANALYSIS)
def test_get_analysis_after_running(mock_claude, client, sample_session):
    session_id = sample_session["id"]
    client.post(
        f"/sessions/{session_id}/ideas",
        json={"participant_id": "p1", "participant_name": "Anna", "content": "Test idea"},
    )
    client.post(f"/sessions/{session_id}/analyse")

    response = client.get(f"/sessions/{session_id}/analysis")
    assert response.status_code == 200
    assert response.json()["framework"] == "swot"


@patch("app.routes.analysis.analyse_ideas", return_value=MOCK_ANALYSIS)
def test_analysis_sets_status_to_analysed(mock_claude, client, sample_session):
    session_id = sample_session["id"]
    client.post(
        f"/sessions/{session_id}/ideas",
        json={"participant_id": "p1", "participant_name": "Anna", "content": "Test"},
    )
    client.post(f"/sessions/{session_id}/analyse")

    response = client.get(f"/sessions/{session_id}")
    assert response.json()["status"] == "analysed"


@patch("app.routes.analysis.analyse_ideas", return_value=MOCK_ANALYSIS)
def test_download_report(mock_claude, client, sample_session):
    session_id = sample_session["id"]
    client.post(
        f"/sessions/{session_id}/ideas",
        json={"participant_id": "p1", "participant_name": "Anna", "content": "Test"},
    )
    client.post(f"/sessions/{session_id}/analyse")

    response = client.get(f"/sessions/{session_id}/report")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 0


def test_download_report_no_analysis(client, sample_session):
    response = client.get(f"/sessions/{sample_session['id']}/report")
    assert response.status_code == 400


def test_download_report_session_not_found(client):
    response = client.get("/sessions/doesnotexist/report")
    assert response.status_code == 404
