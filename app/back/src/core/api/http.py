"""Shared HTTP contract helpers: error envelope, page envelope and rate limiting.

The envelope shape is identical to the one Chunking already publishes, so the
frontend can reuse a single error and pagination handler across every domain.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
import threading
from typing import TypeVar

from fastapi import HTTPException
from pydantic import Field

from ingestion.schemas.common import StrictModel


ItemT = TypeVar("ItemT")

#: Largest page a listing endpoint will ever return.
MAX_PAGE_SIZE = 100

#: Default page size when the caller does not ask for one.
DEFAULT_PAGE_SIZE = 25


class ErrorBodySchema(StrictModel):
    """Body of the shared error envelope."""

    code: str
    message: str
    run_id: str | None = None
    details: dict[str, object] = Field(default_factory=dict)


class ErrorEnvelopeSchema(StrictModel):
    """Every non-2xx response uses this envelope."""

    error: ErrorBodySchema


def http_error(
    *,
    status_code: int,
    code: str,
    message: str,
    run_id: str | None = None,
    details: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
) -> HTTPException:
    """Build an ``HTTPException`` already carrying the shared envelope."""

    return HTTPException(
        status_code=status_code,
        detail=ErrorEnvelopeSchema(
            error=ErrorBodySchema(
                code=code,
                message=message,
                run_id=run_id,
                details=details or {},
            )
        ).model_dump(),
        headers=headers,
    )


class RequestThrottle:
    """In-memory per-client sliding-window throttle (PR-6 rate limiting).

    Same sliding-window algorithm as ``ingestion.gui.server.GuiRegisterThrottle``
    (own copy here rather than an import: that class lives in the raw
    ``http.server`` GUI bridge, a different runtime than FastAPI, and pulling
    ``ingestion.gui`` infra into a shared ``core.api`` helper would be a
    stranger cross-module dependency than the ~15 duplicated lines of
    bookkeeping). Process-local and best-effort by design: acceptable for a
    single-process deployment; a multi-instance deployment needs a shared
    store (Redis) instead — out of scope for this MVP-cleanup pass.
    """

    def __init__(self, *, max_attempts: int, window: timedelta) -> None:
        self._max_attempts = max_attempts
        self._window = window
        self._attempts: dict[str, list[datetime]] = {}
        self._lock = threading.Lock()

    def allow(self, client_key: str, *, now: datetime | None = None) -> bool:
        """Record one attempt for ``client_key``; ``False`` once the window is full."""

        now = now or datetime.now(timezone.utc)
        cutoff = now - self._window
        with self._lock:
            recent = [
                attempted_at
                for attempted_at in self._attempts.get(client_key, [])
                if attempted_at > cutoff
            ]
            if len(recent) >= self._max_attempts:
                self._attempts[client_key] = recent
                return False
            recent.append(now)
            self._attempts[client_key] = recent
            return True


def rate_limit_error(*, code: str, message: str, retry_after_seconds: int) -> HTTPException:
    """Build the shared-envelope 429 raised when a ``RequestThrottle`` rejects a request."""

    return http_error(
        status_code=429,
        code=code,
        message=message,
        headers={"Retry-After": str(retry_after_seconds)},
    )


def paginate(
    items: Sequence[ItemT],
    *,
    page: int,
    page_size: int,
) -> dict[str, object]:
    """Return one page of an already-materialized sequence."""

    total_items = len(items)
    total_pages = (total_items + page_size - 1) // page_size if total_items else 0
    start = (page - 1) * page_size
    return {
        "items": list(items[start : start + page_size]),
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
    }
