import time

import bcrypt
import pytest
from fastapi.testclient import TestClient

from app.auth import (
    COOKIE_NAME,
    LoginLimiter,
    create_session_token,
    get_limiter,
    read_session_token,
)
from app.config import Settings, get_settings
from app.main import app

PASSWORD = "correct horse battery"


@pytest.fixture
def settings():
    # rounds=4 keeps tests fast. Real hashes use 12.
    hashed = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()
    return Settings(username="testuser", password_hash=hashed, session_secret="s" * 40)


@pytest.fixture
def client(settings):
    limiter = LoginLimiter(max_attempts=5, block_seconds=900)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_limiter] = lambda: limiter
    # https base URL, because the session cookie is marked Secure
    yield TestClient(app, base_url="https://testserver")
    app.dependency_overrides.clear()


def login(client, username="testuser", password=PASSWORD):
    return client.post("/login", json={"username": username, "password": password})


def test_login_success_sets_safe_cookie(client):
    response = login(client)
    assert response.status_code == 200
    header = response.headers["set-cookie"].lower()
    assert COOKIE_NAME in header
    assert "httponly" in header
    assert "secure" in header
    assert "samesite=lax" in header
    assert "max-age=86400" in header


def test_wrong_password_and_wrong_username_look_the_same(client):
    wrong_password = login(client, password="nope")
    wrong_username = login(client, username="someone")
    assert wrong_password.status_code == 401
    assert wrong_username.status_code == 401
    assert wrong_password.json() == wrong_username.json()


def test_ask_requires_login(client):
    response = client.post("/ask", json={"question": "How do I post an invoice?"})
    assert response.status_code == 401


def test_ask_works_after_login(client, monkeypatch):
    monkeypatch.setattr("app.routes.answer_question", lambda q: {"answer": "ok", "sources": []})
    login(client)
    response = client.post("/ask", json={"question": "How do I post an invoice?"})
    assert response.status_code == 200

def test_garbage_cookie_is_rejected(client):
    response = client.post(
        "/ask",
        json={"question": "hi"},
        headers={"Cookie": f"{COOKIE_NAME}=not-a-real-token"},
    )
    assert response.status_code == 401


def test_session_older_than_24_hours_is_rejected(client, settings, monkeypatch):
    real_time = time.time
    with monkeypatch.context() as m:
        m.setattr(time, "time", lambda: real_time() - 86401)
        old_token = create_session_token(settings)
    response = client.post(
        "/ask",
        json={"question": "hi"},
        headers={"Cookie": f"{COOKIE_NAME}={old_token}"},
    )
    assert response.status_code == 401


def test_fresh_token_is_accepted(settings):
    token = create_session_token(settings)
    assert read_session_token(token, settings) is not None


def test_token_signed_with_another_secret_is_rejected(settings):
    other = Settings(username="testuser", password_hash="x", session_secret="z" * 40)
    token = create_session_token(other)
    assert read_session_token(token, settings) is None


def test_blocked_after_too_many_failures(client):
    for _ in range(5):
        assert login(client, password="wrong").status_code == 401
    assert login(client, password="wrong").status_code == 429
    # even the correct password is refused while blocked
    assert login(client).status_code == 429


def test_logout_clears_cookie(client):
    login(client)
    response = client.post("/logout")
    assert response.status_code == 200
    assert "max-age=0" in response.headers["set-cookie"].lower()


def test_limiter_block_expires():
    now = [0.0]
    limiter = LoginLimiter(max_attempts=2, block_seconds=60, clock=lambda: now[0])
    limiter.record_failure("a")
    limiter.record_failure("a")
    assert limiter.is_blocked("a")
    now[0] = 61
    assert not limiter.is_blocked("a")


def test_success_resets_failure_count():
    limiter = LoginLimiter(max_attempts=5, block_seconds=60)
    for _ in range(4):
        limiter.record_failure("a")
    limiter.record_success("a")
    for _ in range(4):
        limiter.record_failure("a")
    assert not limiter.is_blocked("a")