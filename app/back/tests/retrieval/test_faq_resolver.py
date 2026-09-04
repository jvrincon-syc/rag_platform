"""FAQ shortcut default: off unless explicitly enabled (PR-1 1.1, docs/adr/ADR-011)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from api.dependencies import _build_faq_resolver


@pytest.fixture(autouse=True)
def _clean_faq_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FAQ_MATCH", raising=False)
    monkeypatch.delenv("FAQ_PATH", raising=False)
    monkeypatch.delenv("FAQ_THRESHOLD", raising=False)


def _write_faq(chunks_root: Path) -> None:
    faq_dir = chunks_root.parent / "faq"
    faq_dir.mkdir(parents=True, exist_ok=True)
    (faq_dir / "sst-faq-80.md").write_text(
        "# FAQ\n\n## Que es el comite?\nEs un organo consultivo.\n",
        encoding="utf-8",
    )


def test_resolver_none_cuando_faq_match_off(tmp_path: Path) -> None:
    chunks_root = tmp_path / "chunks"
    chunks_root.mkdir()
    _write_faq(chunks_root)

    resolver = _build_faq_resolver(chunks_root)

    assert resolver is None


def test_resolver_none_cuando_faq_match_no_seteado(tmp_path: Path) -> None:
    """The operative default is off: an unset ``FAQ_MATCH`` must not enable the shortcut."""
    chunks_root = tmp_path / "chunks"
    chunks_root.mkdir()
    _write_faq(chunks_root)

    assert "FAQ_MATCH" not in os.environ

    resolver = _build_faq_resolver(chunks_root)

    assert resolver is None


def test_resolver_activo_cuando_faq_match_on(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Sanity check: the shortcut can still be opted in explicitly."""
    chunks_root = tmp_path / "chunks"
    chunks_root.mkdir()
    _write_faq(chunks_root)
    monkeypatch.setenv("FAQ_MATCH", "on")

    resolver = _build_faq_resolver(chunks_root)

    assert resolver is not None
