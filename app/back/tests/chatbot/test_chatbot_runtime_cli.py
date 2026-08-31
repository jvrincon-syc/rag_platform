from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from chatbot_runtime.main import main as runtime_main
from chatbot_runtime.settings import RuntimeSettings
from chatbot_runtime.warmup import (
    WarmupStatusSnapshot,
    main as warmup_main,
    run_runtime_warmup,
)


def _runtime_snapshot(*, ready: bool, last_error: str | None = None) -> WarmupStatusSnapshot:
    return WarmupStatusSnapshot(
        ready=ready,
        warmed_embedding=ready,
        warmed_reranker=ready,
        last_error=last_error,
    )


def _stub_runtime(*, ready: bool, closed: list[str]) -> SimpleNamespace:
    return SimpleNamespace(
        app=object(),
        warmup=SimpleNamespace(
            warm=lambda: _runtime_snapshot(ready=ready, last_error="RuntimeError"),
        ),
        services=SimpleNamespace(close=lambda: closed.append("closed")),
    )


def test_run_runtime_warmup_returns_true_and_closes_services(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[str] = []
    monkeypatch.setattr(
        "chatbot_runtime.warmup.build_runtime_from_env",
        lambda *, environ: _stub_runtime(ready=True, closed=closed),
    )

    assert run_runtime_warmup(environ={}) is True
    assert closed == ["closed"]


def test_run_runtime_warmup_returns_false_when_runtime_is_not_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[str] = []
    monkeypatch.setattr(
        "chatbot_runtime.warmup.build_runtime_from_env",
        lambda *, environ: _stub_runtime(ready=False, closed=closed),
    )

    assert run_runtime_warmup(environ={}) is False
    assert closed == ["closed"]


def test_warmup_main_exits_nonzero_when_runtime_warmup_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "chatbot_runtime.warmup.run_runtime_warmup",
        lambda *, environ=None: False,
    )

    with pytest.raises(SystemExit) as error:
        warmup_main()

    assert error.value.code == 1


def test_runtime_main_runs_uvicorn_after_successful_warmup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[str] = []
    uvicorn_calls: dict[str, object] = {}

    monkeypatch.setattr(
        "chatbot_runtime.main.load_runtime_settings",
        lambda environ: RuntimeSettings(api_bind_host="127.0.0.1", api_port=9901),
    )
    monkeypatch.setattr(
        "chatbot_runtime.main.build_chatbot_runtime_from_env",
        lambda *, environ: _stub_runtime(ready=True, closed=closed),
    )
    monkeypatch.setitem(
        sys.modules,
        "uvicorn",
        SimpleNamespace(
            run=lambda app, host, port: uvicorn_calls.update(
                {"app": app, "host": host, "port": port}
            )
        ),
    )

    runtime_main()

    assert uvicorn_calls["host"] == "127.0.0.1"
    assert uvicorn_calls["port"] == 9901
    assert closed == []


def test_runtime_main_fails_closed_when_bge_warmup_does_not_finish(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[str] = []

    monkeypatch.setattr(
        "chatbot_runtime.main.load_runtime_settings",
        lambda environ: RuntimeSettings(),
    )
    monkeypatch.setattr(
        "chatbot_runtime.main.build_chatbot_runtime_from_env",
        lambda *, environ: _stub_runtime(ready=False, closed=closed),
    )

    with pytest.raises(RuntimeError, match="BGE warmup failed before serving traffic"):
        runtime_main()

    assert closed == ["closed"]
