"""G1: ``build_nodes`` propaga ``source_document_revision_id`` al metadata del nodo.

Sin esto, el chatbot no puede construir la cita project-aware
(``/api/projects/{project_id}/document-revisions/{revision_id}/raw``) porque el
dato nunca llega a ``IndexingNodeRecord.metadata`` -> ``RetrievedEvidence.metadata``.
Sigue el mismo patron que ``test_section_context_nodes.py``.
"""

from __future__ import annotations

from embedding.infrastructure.filesystem.chunk_bundle_reader import (
    ChunkBundleContent,
    SourceChildChunk,
    SourceParentChunk,
    SourceSpanRecord,
)
from indexing.application.bundle_first.index_bundle import build_nodes


_PROJECT = "proj_alpha"
_BUNDLE = "cb_doc01"


def _content(*, source_document_revision_id: str | None) -> ChunkBundleContent:
    span = SourceSpanRecord(char_start=0, char_end=4)
    return ChunkBundleContent(
        parents=(
            SourceParentChunk(
                chunk_id="p1",
                document_id="doc01",
                profile_id="local-structural-v2",
                ordinal=0,
                text="parent",
                source_span=span,
                block_ids=["b1"],
            ),
        ),
        children=(
            SourceChildChunk(
                chunk_id="c1",
                parent_id="p1",
                document_id="doc01",
                profile_id="local-structural-v2",
                ordinal=0,
                text="child",
                source_span=span,
                token_count=1,
            ),
        ),
        source_content_fingerprint="f" * 64,
        corpus_version="corpus-1",
        document_id="doc01",
        document_name="doc01.pdf",
        source_relpath="a/doc01.pdf",
        source_hash="a" * 64,
        normalized_relpath="a/doc01.md",
        source_document_revision_id=source_document_revision_id,
    )


def _nodes(content: ChunkBundleContent):
    return build_nodes(
        content=content,
        chunk_bundle_id=_BUNDLE,
        chunking_bundle_fingerprint="f" * 64,
        chunking_version="local-structural-v2",
        ingestion_origin="local",
        project_id=_PROJECT,
    )


def test_build_nodes_propaga_source_document_revision_id() -> None:
    nodes = _nodes(_content(source_document_revision_id="rev-001"))

    assert all(node.metadata["source_document_revision_id"] == "rev-001" for node in nodes)


def test_build_nodes_deja_revision_en_none_cuando_el_bundle_no_la_trae() -> None:
    nodes = _nodes(_content(source_document_revision_id=None))

    assert all(node.metadata["source_document_revision_id"] is None for node in nodes)
