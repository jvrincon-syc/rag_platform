"""GUI auth endpoints migrated to FastAPI.

Provides cookie-based session management: login, session check, logout.
Self-registration is disabled (403) — operators are bootstrapped or
admin-created only.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from core.http_auth import HttpAuthError
from ingestion.gui.auth_session import (
    SESSION_COOKIE_NAME,
    GuiAuthCoordinator,
    GuiSession,
    build_expired_cookie,
    build_session_cookie,
    parse_cookie,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

TRUSTED_GUI_ORIGINS = ("http://127.0.0.1:5173", "http://localhost:5173")


class _LoginRequest(BaseModel):
    username: str
    password: str


class _RegisterRequest(BaseModel):
    username: str
    password: str
    project_scope: list[str] | None = None


class GuiRegisterThrottle:
    """In-memory per-client throttle for unauthenticated GUI registrations."""

    def __init__(
        self,
        *,
        max_attempts: int = 5,
        window: timedelta = timedelta(hours=1),
    ) -> None:
        self._max_attempts = max_attempts
        self._window = window
        self._attempts: dict[str, list[datetime]] = {}
        self._lock = threading.Lock()

    def allow(self, client_key: str, *, now: datetime) -> bool:
        cutoff = now - self._window
        with self._lock:
            recent = [
                t for t in self._attempts.get(client_key, []) if t > cutoff
            ]
            if len(recent) >= self._max_attempts:
                self._attempts[client_key] = recent
                return False
            recent.append(now)
            self._attempts[client_key] = recent
            return True


_register_throttle = GuiRegisterThrottle()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _origin_is_trusted(request: Request) -> bool:
    origin = request.headers.get("origin")
    return origin is None or origin in TRUSTED_GUI_ORIGINS


def _request_uses_tls(request: Request) -> bool:
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    if any(p.strip().lower() == "https" for p in forwarded_proto.split(",")):
        return True
    forwarded = request.headers.get("forwarded", "").lower()
    if "proto=https" in forwarded:
        return True
    return request.url.scheme == "https"


def _get_gui_auth(request: Request) -> GuiAuthCoordinator:
    coordinator: GuiAuthCoordinator | None = getattr(
        request.app.state, "gui_auth", None
    )
    if coordinator is None:
        raise HTTPException(status_code=503, detail="gui auth is not configured")
    return coordinator


async def require_session(
    request: Request,
    coordinator: Annotated[GuiAuthCoordinator, Depends(_get_gui_auth)],
) -> GuiSession:
    """FastAPI dependency: resolve the GUI session from cookie or 401."""
    session_id = parse_cookie(
        request.cookies.get(SESSION_COOKIE_NAME)
        or request.headers.get("cookie"),
        SESSION_COOKIE_NAME,
    )
    session = coordinator.resolve(session_id, now=_utcnow()) if session_id else None
    if session is None:
        raise HTTPException(status_code=401, detail="gui session required")
    return session


@router.get("/session")
async def get_session(
    request: Request,
    coordinator: Annotated[GuiAuthCoordinator, Depends(_get_gui_auth)],
):
    session_id = parse_cookie(
        request.cookies.get(SESSION_COOKIE_NAME)
        or request.headers.get("cookie"),
        SESSION_COOKIE_NAME,
    )
    session = coordinator.resolve(session_id, now=_utcnow()) if session_id else None
    if session is None:
        raise HTTPException(status_code=401, detail="unauthenticated")
    return session.public_metadata()


@router.post("/login")
async def login(
    request: Request,
    body: _LoginRequest,
    coordinator: Annotated[GuiAuthCoordinator, Depends(_get_gui_auth)],
):
    if not _origin_is_trusted(request):
        raise HTTPException(status_code=403, detail="untrusted origin")
    try:
        session = coordinator.login(
            username=body.username.strip(),
            password=body.password,
            now=_utcnow(),
        )
    except HttpAuthError as exc:
        raise HTTPException(
            status_code=exc.http_status,
            detail={"error": {"code": exc.code, "message": str(exc)}},
            headers=dict(exc.response_headers) or None,
        )
    logger.info(
        "GUI session opened",
        extra={"stage": "auth", "event": "gui_session_opened", "principal_id": session.principal_id},
    )
    response = Response(
        content=__import__("json").dumps(session.public_metadata()),
        media_type="application/json",
    )
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session.session_id,
        max_age=coordinator.cookie_max_age,
        httponly=True,
        samesite="strict",
        path="/",
        secure=_request_uses_tls(request),
    )
    return response


@router.post("/register")
async def register(
    request: Request,
    body: _RegisterRequest,
    coordinator: Annotated[GuiAuthCoordinator, Depends(_get_gui_auth)],
):
    """Self-registration disabled — operators must be bootstrapped or admin-created."""
    raise HTTPException(status_code=403, detail="self-registration is disabled")


@router.post("/logout")
async def logout(
    request: Request,
    coordinator: Annotated[GuiAuthCoordinator, Depends(_get_gui_auth)],
):
    if not _origin_is_trusted(request):
        raise HTTPException(status_code=403, detail="untrusted origin")
    session_id = parse_cookie(
        request.cookies.get(SESSION_COOKIE_NAME)
        or request.headers.get("cookie"),
        SESSION_COOKIE_NAME,
    )
    if session_id is not None:
        coordinator.logout(session_id)
    response = Response(content='{"ok": true}', media_type="application/json")
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="strict",
        secure=_request_uses_tls(request),
    )
    return response
