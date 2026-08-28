"""Live smoke test for the real BGE-M3 reranker adapter.

Needs FlagEmbedding + the BAAI/bge-m3 weights available locally (same runtime
as the embedding provider, see indexing/infrastructure/embeddings/bge.py).
Marked bge_runtime like the rest of the BGE-dependent suite -- the operator
runs this, not the implementing agent.
"""

from __future__ import annotations

import pytest

from retrieval.domain.models import RetrievedEvidence
from retrieval.infrastructure.bge_reranker import BgeReranker


def _evidence(node_id: str, *, text: str) -> RetrievedEvidence:
    return RetrievedEvidence(
        node_id=node_id,
        document_id=f"doc-{node_id}",
        child_chunk_id=node_id,
        text=text,
        score=0.0,
        source="vector",
        embedding_profile_id="local-bge-m3-v1",
        corpus_version="corpus-v1",
    )


@pytest.mark.bge_runtime
def test_bge_reranker_ranks_the_literal_answer_above_an_unrelated_passage() -> None:
    pytest.importorskip("FlagEmbedding")

    query = "Como se puede comunicar un trabajador con el COPASST?"
    literal_answer = _evidence(
        "n_correct",
        text="Escribir al correo: copasst@syc.com.co Seguridadysalud@syc.com.co Llamadas y WhatsApp: 3176451139",
    )
    unrelated = _evidence(
        "n_unrelated",
        text="AUDITORIA INTERNA Para determinar la eficacia del Sistema de Gestion de Seguridad y Salud "
        "en el Trabajo, se realizaran auditorias al Sistema de manera anual.",
    )

    result = BgeReranker().rerank(
        query=query, candidates=[unrelated, literal_answer], top_n=2
    )

    assert result[0].node_id == "n_correct"
