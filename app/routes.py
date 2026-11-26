from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.auth import (
    COOKIE_NAME,
    LoginLimiter,
    create_session_token,
    get_limiter,
    require_user,
    verify_credentials,
)
from app.config import Settings, get_settings

router = APIRouter()


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
    # Stub: retrieval and the LLM come later.
    return {"answer": "Placeholder: retrieval is not built yet.", "sources": []}