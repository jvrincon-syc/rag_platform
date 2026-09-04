"""G1: el reader de bundles debe leer ``source_document_revision_id`` del sidecar.

El escritor (``chunking/infrastructure/filesystem_chunk_repository.py``) ya
graba este campo en el JSON de metadata; hasta este cambio el reader nunca lo
leia de vuelta, asi que nunca llegaba a ``ChunkBundleContent`` ni, por lo
tanto, a los nodos de indexacion ni a la cita del chatbot (ver G1 del plan
2026-09-04-convergencia-mvp-limpieza.md).
"""

from __future__ import annotations

import json
from pathlib import Path

from embedding.infrastructure.filesystem.chunk_bundle_reader import (
    CHILD_SUFFIX,
    METADATA_SUFFIX,
    PARENT_SUFFIX,
    FilesystemChunkBundleContentReader,
)


def _write_bundle(root: Path, *, source_document_revision_id: str | None) -> str:
    stem = root / "doc01"
    metadata_path = Path(str(stem) + METADATA_SUFFIX)
    parent_path = Path(str(stem) + PARENT_SUFFIX)
    child_path = Path(str(stem) + CHILD_SUFFIX)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(
            {
                "document_id": "doc01",
                "document_name": "doc01.pdf",
                "source_relpath": "a/doc01.pdf",
                "source_hash": "a" * 64,
                "corpus_version": "corpus-1",
                "normalized_relpath": "a/doc01.md",
                "source_document_revision_id": source_document_revision_id,
            }
        ),
        encoding="utf-8",
    )
    parent_path.write_text(
        json.dumps(
            {
                "chunk_id": "p1",
                "document_id": "doc01",
                "profile_id": "local-structural-v2",
                "ordinal": 0,
                "text": "parent",
                "source_span": {"char_start": 0, "char_end": 4},
                "block_ids": ["b1"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    child_path.write_text(
        json.dumps(
            {
                "chunk_id": "c1",
                "parent_id": "p1",
                "document_id": "doc01",
                "profile_id": "local-structural-v2",
                "ordinal": 0,
                "text": "child",
                "source_span": {"char_start": 0, "char_end": 4},
                "token_count": 1,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return str(metadata_path.relative_to(root))


def test_reader_propaga_source_document_revision_id_desde_el_sidecar(tmp_path: Path) -> None:
    relpath = _write_bundle(tmp_path, source_document_revision_id="rev-001")
    reader = FilesystemChunkBundleContentReader(chunks_root=tmp_path)

    content = reader.read(artifact_relpath=relpath)

    assert content.source_document_revision_id == "rev-001"


def test_reader_deja_revision_en_none_cuando_el_sidecar_no_la_trae(tmp_path: Path) -> None:
    relpath = _write_bundle(tmp_path, source_document_revision_id=None)
    reader = FilesystemChunkBundleContentReader(chunks_root=tmp_path)

    content = reader.read(artifact_relpath=relpath)

    assert content.source_document_revision_id is None
