import os
from dataclasses import dataclass

REQUIRED_VARS = ("APP_USERNAME", "APP_PASSWORD_HASH", "SESSION_SECRET")
MIN_SECRET_LENGTH = 32


@dataclass(frozen=True)
class Settings:
    username: str
    password_hash: str
    session_secret: str
    session_max_age: int = 24 * 60 * 60  # 24 hours, in seconds


def load_settings() -> Settings:
    missing = [name for name in REQUIRED_VARS if not os.environ.get(name, "").strip()]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    secret = os.environ["SESSION_SECRET"]
    if len(secret) < MIN_SECRET_LENGTH:
        raise RuntimeError(f"SESSION_SECRET must be at least {MIN_SECRET_LENGTH} characters")

    return Settings(
        username=os.environ["APP_USERNAME"],
        password_hash=os.environ["APP_PASSWORD_HASH"],
        session_secret=secret,
    )