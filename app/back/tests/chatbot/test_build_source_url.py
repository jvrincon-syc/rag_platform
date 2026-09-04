"""G1: ``_build_source_url`` emite la ruta project-aware cuando hay revision id.

Cierra el gap documentado en plans/2026-09-04-mvp/PR-1-invariants.md (seccion
1.7, "Known gap"): el dato ya viaja en la evidencia (ver
test_source_document_revision_propagation.py + test_chunk_bundle_reader_revision_id.py),
asi que el emisor debe preferir
``/api/projects/{project_id}/document-revisions/{revision_id}/raw`` y solo caer
a la ruta legacy deprecada cuando falta la revision (p. ej. evidencia FAQ).
"""

from __future__ import annotations

import pytest

from chatbot.domain.models import ChatbotWebhookChunk
from retrieval.domain.models import RetrievedEvidence


def _evidence(**metadata_overrides: object) -> RetrievedEvidence:
    metadata: dict[str, object] = {
        "source_relpath": "a/doc01.pdf",
        "project_id": "proj_alpha",
        "source_document_revision_id": "rev-001",
    }
    metadata.update(metadata_overrides)
    return RetrievedEvidence(
        node_id="node-1",
        document_id="doc01",
        child_chunk_id="node-1",
        text="texto",
        score=1.0,
        source="vector",
        metadata=metadata,
        embedding_profile_id="profile-1",
        corpus_version="corpus-1",
    )


@pytest.fixture(autouse=True)
def _base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SST_DOCUMENTS_BASE_URL", "https://docs.example.com")


def test_emite_ruta_project_aware_cuando_hay_project_id_y_revision() -> None:
    chunk = ChatbotWebhookChunk.from_evidence(_evidence())

    assert chunk.metadata["source_url"] == (
        "https://docs.example.com/api/projects/proj_alpha"
        "/document-revisions/rev-001/raw"
    )


def test_cae_a_la_ruta_legacy_cuando_falta_la_revision() -> None:
    chunk = ChatbotWebhookChunk.from_evidence(
        _evidence(source_document_revision_id=None)
    )

    assert chunk.metadata["source_url"] == (
        "https://docs.example.com/api/documents/raw/a/doc01.pdf"
    )


def test_sin_base_url_no_hay_source_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SST_DOCUMENTS_BASE_URL", raising=False)

    chunk = ChatbotWebhookChunk.from_evidence(_evidence())

    assert "source_url" not in chunk.metadata
