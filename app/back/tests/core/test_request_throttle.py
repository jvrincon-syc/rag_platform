"""PR-6: ``RequestThrottle`` sliding-window behavior (deterministic, no HTTP)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.api.http import RequestThrottle

_T0 = datetime(2026, 9, 4, 12, 0, 0, tzinfo=timezone.utc)


def test_permite_hasta_el_limite_y_luego_rechaza() -> None:
    throttle = RequestThrottle(max_attempts=3, window=timedelta(minutes=1))

    assert throttle.allow("actor-1", now=_T0) is True
    assert throttle.allow("actor-1", now=_T0) is True
    assert throttle.allow("actor-1", now=_T0) is True
    assert throttle.allow("actor-1", now=_T0) is False


def test_claves_distintas_tienen_cupos_independientes() -> None:
    throttle = RequestThrottle(max_attempts=1, window=timedelta(minutes=1))

    assert throttle.allow("actor-1", now=_T0) is True
    assert throttle.allow("actor-1", now=_T0) is False
    assert throttle.allow("actor-2", now=_T0) is True


def test_la_ventana_desliza_y_libera_cupo_expirado() -> None:
    throttle = RequestThrottle(max_attempts=1, window=timedelta(minutes=1))

    assert throttle.allow("actor-1", now=_T0) is True
    assert throttle.allow("actor-1", now=_T0 + timedelta(seconds=30)) is False
    # Past the window: the first attempt expired, budget is available again.
    assert throttle.allow("actor-1", now=_T0 + timedelta(minutes=1, seconds=1)) is True
