"""FAQ shortcut: default on/off gate (PR-1 1.1) + per-project isolation (PR-3 3.1/3.2).

PR-1 1.1 originally flipped the operative default to ``off`` as a P0 stop-gap for the
cross-project leak in the old single global resolver (``sorted(glob(...))[0]``). PR-3 replaced
that resolver with ``FaqResolverRegistry`` — one resolver per ``project_id``, no glob, no
``matches[0]`` — and re-enables the shortcut by default (3.4) now that isolation is in place.
``_build_faq_resolver`` was renamed to ``_build_faq_registry`` and now returns a registry, not a
single resolver: the contract changed from "load the one FAQ file" to "look up a project's FAQ
file on demand", so these tests were rewritten rather than left asserting the old shape.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from api.dependencies import _build_faq_registry
from retrieval.infrastructure.faq_resolver import FaqResolverRegistry


@pytest.fixture(autouse=True)
def _clean_faq_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FAQ_MATCH", raising=False)
    monkeypatch.delenv("FAQ_PATH", raising=False)
    monkeypatch.delenv("FAQ_THRESHOLD", raising=False)


def _write_project_faq(data_root: Path, project_id: str, qa: tuple[str, str]) -> None:
    """Write the FAQ file at the slug directory ``FaqResolverRegistry`` resolves for ``project_id``.

    ``FaqResolverRegistry`` strips the ``proj_`` prefix (same convention as
    ``ProjectStorageResolver``): ``project_id="proj_demo"`` resolves to
    ``projects/demo/faq/sst-faq-80.md``, not ``projects/proj_demo/...``.
    """

    slug = project_id[len("proj_"):] if project_id.startswith("proj_") else project_id
    faq_dir = data_root / "projects" / slug / "faq"
    faq_dir.mkdir(parents=True, exist_ok=True)
    question, answer = qa
    (faq_dir / "sst-faq-80.md").write_text(
        f"## FAQ-1\n```yaml\nquestion: {question}\nanswer: {answer}\n```\n",
        encoding="utf-8",
    )


def test_registry_none_cuando_faq_match_off(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    chunks_root = tmp_path / "chunks"
    chunks_root.mkdir()
    _write_project_faq(tmp_path, "proj_demo", ("Que es el comite?", "Es un organo consultivo."))
    monkeypatch.setenv("FAQ_MATCH", "off")

    assert _build_faq_registry(chunks_root) is None


def test_registry_activo_cuando_faq_match_no_seteado(tmp_path: Path) -> None:
    """PR-3 3.4: the operative default is on again — unset ``FAQ_MATCH`` enables the shortcut."""
    chunks_root = tmp_path / "chunks"
    chunks_root.mkdir()

    assert "FAQ_MATCH" not in os.environ

    registry = _build_faq_registry(chunks_root)

    assert isinstance(registry, FaqResolverRegistry)


def test_registry_resuelve_faq_de_un_proyecto_cuando_hay_archivo(tmp_path: Path) -> None:
    chunks_root = tmp_path / "chunks"
    chunks_root.mkdir()
    _write_project_faq(tmp_path, "proj_demo", ("Que es el comite?", "Es un organo consultivo."))

    registry = _build_faq_registry(chunks_root)

    assert isinstance(registry, FaqResolverRegistry)
    resolver = registry.resolver_for("proj_demo")
    assert resolver is not None
    match = resolver.match("Que es el comite?")
    assert match is not None
    assert match.answer == "Es un organo consultivo."


def test_faq_registry_no_cruza_proyectos(tmp_path: Path) -> None:
    """PR-3 3.1/3.2 regression: project A's question never resolves via project B's FAQ file."""
    _write_project_faq(tmp_path, "proj_alpha", ("Cual es el horario del comite?", "8am a 5pm."))
    _write_project_faq(
        tmp_path, "proj_beta", ("Cual es la politica de vacaciones?", "20 dias habiles.")
    )
    registry = FaqResolverRegistry(data_root=tmp_path, threshold=0.85)

    alpha_resolver = registry.resolver_for("proj_alpha")
    beta_resolver = registry.resolver_for("proj_beta")

    assert alpha_resolver is not None and beta_resolver is not None
    # Alpha's own question hits; beta's question (a different file) does not exist for alpha.
    assert alpha_resolver.match("Cual es el horario del comite?") is not None
    assert alpha_resolver.match("Cual es la politica de vacaciones?") is None
    assert beta_resolver.match("Cual es la politica de vacaciones?") is not None
    assert beta_resolver.match("Cual es el horario del comite?") is None


def test_registry_resolver_for_none_cuando_proyecto_no_tiene_faq(tmp_path: Path) -> None:
    registry = FaqResolverRegistry(data_root=tmp_path, threshold=0.85)

    assert registry.resolver_for("proj_sin_faq") is None
