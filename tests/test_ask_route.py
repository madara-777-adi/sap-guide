import psycopg
import pytest
from fastapi.testclient import TestClient

from app.answer import ProvidersUnavailable
from app.auth import require_user
from app.main import app


@pytest.fixture
def client():
    app.dependency_overrides[require_user] = lambda: "testuser"
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_ask_returns_the_result(client, monkeypatch):
    monkeypatch.setattr("app.routes.answer_question", lambda q: {"answer": "ok", "sources": []})
    response = client.post("/ask", json={"question": "hi"})
    assert response.status_code == 200
    assert response.json()["answer"] == "ok"


def test_busy_providers_give_503_without_details(client, monkeypatch):
    def boom(question):
        raise ProvidersUnavailable("All providers failed: groq-120b: RateLimitError")

    monkeypatch.setattr("app.routes.answer_question", boom)
    response = client.post("/ask", json={"question": "hi"})
    assert response.status_code == 503
    assert "groq" not in response.text.lower()


def test_database_error_gives_503_without_details(client, monkeypatch):
    def boom(question):
        raise psycopg.OperationalError("connection to ep-secret-host.neon.tech failed")

    monkeypatch.setattr("app.routes.answer_question", boom)
    response = client.post("/ask", json={"question": "hi"})
    assert response.status_code == 503
    assert "neon" not in response.text.lower()