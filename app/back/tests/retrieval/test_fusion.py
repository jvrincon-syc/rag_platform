from __future__ import annotations

from retrieval.fusion import (
    RetrievedCandidate,
    reciprocal_rank_fusion,
    vector_primary_hybrid_fusion,
)
from retrieval.reranking import preserve_order_reranker


def test_reciprocal_rank_fusion_deduplicates_by_node_id_and_keeps_sources() -> None:
    vector = [
        RetrievedCandidate("n1", "texto", 0.9, "vector", {"page_number": 1}),
        RetrievedCandidate("n2", "otro", 0.8, "vector", {"page_number": 2}),
    ]
    lexical = [
        RetrievedCandidate("n2", "otro", 12.0, "lexical", {"page_number": 2}),
        RetrievedCandidate("n3", "mas", 4.0, "lexical", {"page_number": 3}),
    ]

    fused = reciprocal_rank_fusion([vector, lexical], k=60)

    assert [item.node_id for item in fused] == ["n2", "n1", "n3"]
    assert fused[0].metadata["retrieval_sources"] == ["vector", "lexical"]


def test_vector_primary_hybrid_fusion_rescue_below_vector_backed() -> None:
    vector = [
        RetrievedCandidate("n1", "a", 0.9, "vector", {}),
        RetrievedCandidate("n2", "b", 0.8, "vector", {}),
    ]
    lexical = [
        RetrievedCandidate("n3", "c", 5.0, "lexical", {}),
    ]

    fused = vector_primary_hybrid_fusion(vector, lexical)

    ids = [c.node_id for c in fused]
    assert ids == ["n1", "n2", "n3"]
    assert fused[2].score < fused[1].score


def test_vector_primary_hybrid_fusion_boosts_vector_plus_lexical() -> None:
    vector = [
        RetrievedCandidate("n1", "a", 0.9, "vector", {}),
        RetrievedCandidate("n2", "b", 0.8, "vector", {}),
    ]
    lexical = [
        RetrievedCandidate("n2", "b", 5.0, "lexical", {}),
    ]

    fused = vector_primary_hybrid_fusion(vector, lexical, lexical_boost=0.5)

    n2 = next(c for c in fused if c.node_id == "n2")
    n1 = next(c for c in fused if c.node_id == "n1")
    assert n2.score > n1.score


def test_vector_primary_hybrid_fusion_empty() -> None:
    assert vector_primary_hybrid_fusion([], []) == []


def test_preserve_order_reranker_marks_original_scores() -> None:
    candidate = RetrievedCandidate("n1", "texto", 0.9, "vector", {})

    reranked = preserve_order_reranker([candidate])

    assert reranked[0].score == 0.9
    assert reranked[0].metadata["original_score"] == 0.9
