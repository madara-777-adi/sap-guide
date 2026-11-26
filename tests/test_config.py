import pytest

from app.config import load_settings


def set_valid_env(monkeypatch):
    monkeypatch.setenv("APP_USERNAME", "testuser")
    monkeypatch.setenv("APP_PASSWORD_HASH", "not-a-real-hash")
    monkeypatch.setenv("SESSION_SECRET", "x" * 40)


def test_loads_when_all_set(monkeypatch):
    set_valid_env(monkeypatch)
    settings = load_settings()
    assert settings.username == "testuser"
    assert settings.session_max_age == 86400


def test_one_missing_variable_is_named(monkeypatch):
    set_valid_env(monkeypatch)
    monkeypatch.delenv("APP_USERNAME", raising=False)
    with pytest.raises(RuntimeError, match="APP_USERNAME"):
        load_settings()


def test_all_missing_variables_are_named(monkeypatch):
    for name in ("APP_USERNAME", "APP_PASSWORD_HASH", "SESSION_SECRET"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(RuntimeError) as exc_info:
        load_settings()
    message = str(exc_info.value)
    assert "APP_USERNAME" in message
    assert "APP_PASSWORD_HASH" in message
    assert "SESSION_SECRET" in message


def test_empty_value_counts_as_missing(monkeypatch):
    set_valid_env(monkeypatch)
    monkeypatch.setenv("APP_PASSWORD_HASH", "   ")
    with pytest.raises(RuntimeError, match="APP_PASSWORD_HASH"):
        load_settings()


def test_short_secret_is_rejected(monkeypatch):
    set_valid_env(monkeypatch)
    monkeypatch.setenv("SESSION_SECRET", "short")
    with pytest.raises(RuntimeError, match="at least 32"):
        load_settings()


def test_error_message_does_not_leak_values(monkeypatch):
    set_valid_env(monkeypatch)
    monkeypatch.setenv("APP_USERNAME", "distinctive_user_123")
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    with pytest.raises(RuntimeError) as exc_info:
        load_settings()
    assert "distinctive_user_123" not in str(exc_info.value)