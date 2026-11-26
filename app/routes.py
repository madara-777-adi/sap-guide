import logging

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.answer import ProvidersUnavailable
from app.auth import (
    COOKIE_NAME,
    LoginLimiter,
    create_session_token,
    get_limiter,
    require_user,
    verify_credentials,
)
from app.config import Settings, get_settings
from app.qa import answer_question

router = APIRouter()
logger = logging.getLogger(__name__)


class LoginBody(BaseModel):
    username: str = Field(max_length=128)
    password: str = Field(max_length=128)


class AskBody(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


@router.post("/login")
def login(
    body: LoginBody,
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
    limiter: LoginLimiter = Depends(get_limiter),
):
    client_key = request.client.host if request.client else "unknown"

    if limiter.is_blocked(client_key):
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again later.")

    if not verify_credentials(body.username, body.password, settings):
        limiter.record_failure(client_key)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    limiter.record_success(client_key)
    response.set_cookie(
        COOKIE_NAME,
        create_session_token(settings),
        max_age=settings.session_max_age,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return {"status": "ok"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, httponly=True, secure=True, samesite="lax")
    return {"status": "ok"}


@router.post("/ask")
def ask(body: AskBody, _user: str = Depends(require_user)):
    try:
        return answer_question(body.question)
    except ProvidersUnavailable as exc:
        logger.warning("LLM providers unavailable: %s", exc)  # provider names and error types only
        raise HTTPException(
            status_code=503, detail="The answer service is busy. Try again in a minute."
        ) from None
    except psycopg.Error as exc:
        logger.warning("Database error: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503, detail="The document database is not reachable. Try again shortly."
        ) from None