from __future__ import annotations

from retrieval.domain.models import RetrievedEvidence
from retrieval.reranking import NoOpReranker


def _evidence(node_id: str, *, score: float) -> RetrievedEvidence:
    return RetrievedEvidence(
        node_id=node_id,
        document_id=f"doc-{node_id}",
        child_chunk_id=node_id,
        text="texto",
        score=score,
        source="vector",
        embedding_profile_id="local-bge-m3-v1",
        corpus_version="corpus-v1",
    )


def test_no_op_reranker_preserves_order_and_cuts_to_top_n() -> None:
    candidates = [_evidence("n1", score=0.9), _evidence("n2", score=0.8), _evidence("n3", score=0.7)]

    result = NoOpReranker().rerank(query="q", candidates=candidates, top_n=2)

    assert [item.node_id for item in result] == ["n1", "n2"]


def test_no_op_reranker_empty_candidates() -> None:
    assert NoOpReranker().rerank(query="q", candidates=[], top_n=5) == []
