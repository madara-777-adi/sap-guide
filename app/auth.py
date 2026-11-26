import secrets
import time

import bcrypt
from fastapi import Depends, HTTPException, Request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.config import Settings, get_settings

COOKIE_NAME = "sapguide_session"
MAX_FAILED_ATTEMPTS = 5
BLOCK_SECONDS = 15 * 60


def verify_credentials(username: str, password: str, settings: Settings) -> bool:
    # Compute both checks every time, so a wrong username isn't faster than a wrong password.
    username_ok = secrets.compare_digest(username.encode(), settings.username.encode())
    try:
        password_ok = bcrypt.checkpw(password.encode(), settings.password_hash.encode())
    except ValueError:  # malformed hash or over-long password
        password_ok = False
    return username_ok and password_ok


def _serializer(settings: Settings) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.session_secret, salt="sapguide-session")


def create_session_token(settings: Settings) -> str:
    return _serializer(settings).dumps({"user": settings.username})


def read_session_token(token: str, settings: Settings) -> dict | None:
    try:
        data = _serializer(settings).loads(token, max_age=settings.session_max_age)
    except BadSignature:  # also covers expired tokens
        return None
    if data.get("user") != settings.username:
        return None
    return data


def require_user(request: Request, settings: Settings = Depends(get_settings)) -> str:
    token = request.cookies.get(COOKIE_NAME)
    if not token or read_session_token(token, settings) is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    return settings.username


class LoginLimiter:
    """Counts failed logins per client and blocks after too many. In memory only."""

    def __init__(self, max_attempts: int, block_seconds: int, clock=time.monotonic):
        self.max_attempts = max_attempts
        self.block_seconds = block_seconds
        self._clock = clock
        self._failures: dict[str, int] = {}
        self._blocked_until: dict[str, float] = {}

    def is_blocked(self, key: str) -> bool:
        until = self._blocked_until.get(key)
        if until is None:
            return False
        if self._clock() >= until:
            self._blocked_until.pop(key, None)
            self._failures.pop(key, None)
            return False
        return True

    def record_failure(self, key: str) -> None:
        count = self._failures.get(key, 0) + 1
        self._failures[key] = count
        if count >= self.max_attempts:
            self._blocked_until[key] = self._clock() + self.block_seconds

    def record_success(self, key: str) -> None:
        self._failures.pop(key, None)
        self._blocked_until.pop(key, None)


_limiter = LoginLimiter(MAX_FAILED_ATTEMPTS, BLOCK_SECONDS)


def get_limiter() -> LoginLimiter:
    return _limiter