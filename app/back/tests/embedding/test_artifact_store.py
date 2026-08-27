"""Unit tests for Windows-resilient promotion in the artifact store.

``promote()`` must stay atomic (single ``os.replace``, no copy/move fallback)
while tolerating transient sharing violations raised by antivirus, the
indexer or any other short-lived handle holder on Windows.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import embedding.infrastructure.filesystem.artifact_store as artifact_store_module
from embedding.domain.errors import EmbeddingBundleInvalid
from embedding.infrastructure.filesystem.artifact_store import (
    FilesystemEmbeddingBundleArtifactStore,
)


def _stage_bundle(store: FilesystemEmbeddingBundleArtifactStore) -> None:
    store.stage(
        embedding_bundle_id="bundle-1",
        manifest={"provider": "mock", "model": "m", "dimension": 2},
        vectors=[[1.0, 0.0], [0.0, 1.0]],
        chunk_map=[{"chunk_id": "c1"}, {"chunk_id": "c2"}],
    )


def _windows_permission_error(winerror: int) -> PermissionError:
    return PermissionError(13, "Acceso denegado", None, winerror)


def test_promote_reintenta_ante_lock_transitorio_de_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = FilesystemEmbeddingBundleArtifactStore(root=tmp_path / "embeddings")
    _stage_bundle(store)

    real_replace = artifact_store_module.os.replace
    attempts = {"count": 0}

    def flaky_replace(src: object, dst: object) -> None:
        attempts["count"] += 1
        if attempts["count"] <= 2:
            raise _windows_permission_error(5)
        real_replace(src, dst)  # type: ignore[arg-type]

    monkeypatch.setattr(artifact_store_module.os, "replace", flaky_replace)
    monkeypatch.setattr(artifact_store_module.time, "sleep", lambda _seconds: None)

    refs = store.promote(embedding_bundle_id="bundle-1")

    assert attempts["count"] == 3
    assert refs.shape == "2x2"
    assert not (tmp_path / "embeddings" / "_staging" / "bundle-1").exists()
    assert (tmp_path / "embeddings" / "bundle-1" / "vectors.npy").exists()
    assert (tmp_path / "embeddings" / "bundle-1" / "manifest.json").exists()


def test_promote_falla_cerrado_cuando_el_lock_persiste(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = FilesystemEmbeddingBundleArtifactStore(root=tmp_path / "embeddings")
    _stage_bundle(store)

    def locked_replace(src: object, dst: object) -> None:
        raise _windows_permission_error(5)

    monkeypatch.setattr(artifact_store_module.os, "replace", locked_replace)
    monkeypatch.setattr(artifact_store_module.time, "sleep", lambda _seconds: None)

    with pytest.raises(PermissionError):
        store.promote(embedding_bundle_id="bundle-1")

    assert (tmp_path / "embeddings" / "_staging" / "bundle-1" / "vectors.npy").exists()
    assert not (tmp_path / "embeddings" / "bundle-1").exists()


def test_promote_reporta_bundle_sellado_cuando_otro_actor_publico_primero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Race: otro proceso promueve el bundle mientras esperamos el lock."""

    store = FilesystemEmbeddingBundleArtifactStore(root=tmp_path / "embeddings")
    _stage_bundle(store)

    real_replace = artifact_store_module.os.replace

    def racing_replace(src: object, dst: object) -> None:
        real_replace(src, dst)  # type: ignore[arg-type]
        raise _windows_permission_error(32)

    monkeypatch.setattr(artifact_store_module.os, "replace", racing_replace)
    monkeypatch.setattr(artifact_store_module.time, "sleep", lambda _seconds: None)

    with pytest.raises(EmbeddingBundleInvalid, match="already exist"):
        store.promote(embedding_bundle_id="bundle-1")
