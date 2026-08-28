from __future__ import annotations

from retrieval.fusion import (
    RetrievedCandidate,
    reciprocal_rank_fusion,
    vector_primary_hybrid_fusion,
)


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


def test_vector_primary_hybrid_fusion_deep_pool_lexical_hit_does_not_beat_top_vector_rank() -> None:
    """Regression: q13/q21 in retrieval_hybrid_live_report.md.

    Live symptom: ``funciones_copasst.md`` (q13, vector rank ~62 of a 96
    overfetch pool) and ``auditoria_info.md`` (q21, vector rank ~28) were each
    the LONE lexical hit for their query and jumped to fused rank #1, above
    the document containing the literal answer (``verificacion_info.md`` /
    ``copasst/comunicacion.md``, both real vector rank 1). Root cause: RRF
    summed the vector rank (however deep) with the lexical rank, and that sum
    alone -- before any extra boost -- already exceeded a real rank-1 score.
    ``vector_rank_ceiling`` excludes pool noise below rank 20 from ever
    entering the vector+lexical tier; it falls to the lexical-rescue floor
    instead (still ranked below every real vector-backed candidate).
    """
    top_vector_match = RetrievedCandidate("correct_doc", "contiene la respuesta literal", 0.0, "vector", {})
    filler = [
        RetrievedCandidate(f"filler_{i}", "relleno semantico", 0.0, "vector", {})
        for i in range(24)
    ]
    weak_deep_match = RetrievedCandidate("incidental_doc", "coincidencia incidental", 0.0, "vector", {})
    vector = [top_vector_match, *filler, weak_deep_match]  # weak_deep_match at vector rank 26

    lexical = [
        RetrievedCandidate("incidental_doc", "coincidencia incidental", 5.0, "lexical", {}),
    ]

    fused = vector_primary_hybrid_fusion(vector, lexical)

    assert fused[0].node_id == "correct_doc"
    incidental = next(c for c in fused if c.node_id == "incidental_doc")
    assert incidental.score < fused[0].score


def test_vector_primary_hybrid_fusion_pure_vector_query_unaffected_by_ceiling() -> None:
    """Anchor: q56 in retrieval_hybrid_live_report.md (zero lexical candidates).

    When lexical returns nothing, fusion must reduce to plain vector rank
    order -- confirms the ceiling/boost changes don't touch vector-only
    queries at all.
    """
    vector = [
        RetrievedCandidate("n1", "a", 0.0, "vector", {}),
        RetrievedCandidate("n2", "b", 0.0, "vector", {}),
        RetrievedCandidate("n3", "c", 0.0, "vector", {}),
    ]

    fused = vector_primary_hybrid_fusion(vector, [])

    assert [c.node_id for c in fused] == ["n1", "n2", "n3"]
