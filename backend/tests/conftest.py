import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

from app.database import Base
from app.dependencies import get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///file::memory:?cache=shared&uri=true"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_session(client):
    response = client.post(
        "/sessions",
        json={"topic": "Test Workshop", "framework": "swot"},
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def sample_session_with_participant(client, sample_session):
    session_id = sample_session["id"]
    client.post(f"/sessions/{session_id}/join?name=Anna")
    return sample_session


@pytest.fixture
def auth_headers():
    """Return a helper that builds Authorization headers from a session dict.

    Usage in tests: ``headers = auth_headers(sample_session)``
    """
    def _build(session: dict) -> dict:
        return {"Authorization": f"Bearer {session['facilitator_token']}"}
    return _build
