"""Reranker wiring in ``RetrievalSearchService._fuse_and_dedup``.

Only exercises the fuse/dedup/rerank tail -- the other ports aren't touched by
that method, so they're left unset. Full end-to-end search() flow is covered
by ``test_hybrid_search_fusion.py``.
"""

from __future__ import annotations

from retrieval.application.retrieval_service import RetrievalSearchService
from retrieval.domain.models import RetrievedEvidence


def _evidence(node_id: str, *, text: str, score: float) -> RetrievedEvidence:
    return RetrievedEvidence(
        node_id=node_id,
        document_id=f"doc-{node_id}",
        parent_node_id=f"parent-{node_id}",
        child_chunk_id=node_id,
        text=text,
        score=score,
        source="vector",
        embedding_profile_id="local-bge-m3-v1",
        corpus_version="corpus-v1",
    )


class _StubReranker:
    """Deterministic stand-in for a real relevance judge: longer text wins."""

    def rerank(self, *, query, candidates, top_n):
        return sorted(candidates, key=lambda c: len(c.text), reverse=True)[:top_n]


def _service(reranker=None) -> RetrievalSearchService:
    return RetrievalSearchService(
        retrieval_profiles=None,  # type: ignore[arg-type]
        profiles=None,  # type: ignore[arg-type]
        targets=None,  # type: ignore[arg-type]
        query_embedding=None,  # type: ignore[arg-type]
        vector_search=None,  # type: ignore[arg-type]
        lexical_search=None,  # type: ignore[arg-type]
        parent_expansion=None,  # type: ignore[arg-type]
        reranker=reranker,
    )


def test_fuse_and_dedup_defaults_to_no_op_reranker_preserving_fusion_order() -> None:
    vector = [
        _evidence("n1", text="mejor rango vector", score=0.9),
        _evidence("n2", text="peor rango vector pero texto mucho mas largo", score=0.8),
    ]

    result = _service()._fuse_and_dedup(
        vector_candidates=vector, lexical_candidates=[], query="q", top_k=2
    )

    assert [item.node_id for item in result] == ["n1", "n2"]


def test_fuse_and_dedup_uses_injected_reranker_to_override_fusion_order() -> None:
    """q04/q32-style near-tie: RRF's rank gap alone can't tell which candidate
    is truly relevant (see retrieval/fusion.py docstring) -- a real reranker
    judging content can. This proves the wiring lets it override fusion order.
    """
    vector = [
        _evidence("n1", text="corto", score=0.9),
        _evidence("n2", text="mucho mas largo y con mas contenido relevante", score=0.8),
    ]

    result = _service(reranker=_StubReranker())._fuse_and_dedup(
        vector_candidates=vector, lexical_candidates=[], query="q", top_k=2
    )

    assert [item.node_id for item in result] == ["n2", "n1"]


def _q15_shape_candidates():
    """Reproduces q15's live shape: 20 vector-only fillers rank above the
    real ARL-responsibilities chunk (vector rank ~24, past
    vector_rank_ceiling=20), which is also the sole lexical hit.
    """
    vector = [_evidence(f"filler_{i}", text=f"relleno semantico sin relacion numero {i}", score=0.0) for i in range(20)]
    vector.append(
        _evidence(
            "arl_doc",
            text="Capacitar al Comite Paritario de Seguridad y Salud en el Trabajo... "
            "responsabilidades de la ARL en seguridad y salud en el trabajo.",
            score=0.0,
        )
    )
    lexical = [
        RetrievedEvidence(
            node_id="arl_doc",
            document_id="doc-arl_doc",
            child_chunk_id="arl_doc",
            text="Capacitar al Comite Paritario de Seguridad y Salud en el Trabajo... "
            "responsabilidades de la ARL en seguridad y salud en el trabajo.",
            score=5.0,
            source="lexical",
            embedding_profile_id="local-bge-m3-v1",
            corpus_version="corpus-v1",
        )
    ]
    return vector, lexical


def test_fuse_and_dedup_no_op_reranker_loses_deep_rescue_candidate() -> None:
    """Regression: q15 in retrieval_hybrid_live_report.md, BEFORE the reranker fix.

    vector_rank_ceiling correctly excludes the ARL doc from the false-boost
    tier (q13/q21 fix, still holds), but with the default NoOpReranker the
    rescue tier is appended strictly after all vector_rank_ceiling=20
    candidates and top_k=8 only ever looks at the front -- so a genuinely
    answer-bearing rescue candidate is silently dropped, regardless of how
    strong its lexical match is. This is the exact gap the live suite hit for
    Q15 (ARL responsibilities never reached the final 8 despite a strict-mode
    lexical hit).
    """
    vector, lexical = _q15_shape_candidates()

    result = _service()._fuse_and_dedup(  # default reranker = NoOpReranker
        vector_candidates=vector, lexical_candidates=lexical, query="ARL responsabilidades", top_k=8
    )

    assert "arl_doc" not in [item.node_id for item in result]


def test_fuse_and_dedup_real_reranker_rescues_relevant_deep_lexical_hit() -> None:
    """Fix: a reranker that actually judges content (stub standing in for
    BgeReranker) sees the rescue tier too (it's already inside rerank_pool,
    see retrieval_service.py's _RERANK_POOL_SIZE) and can promote a genuinely
    relevant deep candidate into the final top_k -- without any change to the
    fusion/ceiling logic that fixed q13/q21.
    """
    vector, lexical = _q15_shape_candidates()

    result = _service(reranker=_StubReranker())._fuse_and_dedup(
        vector_candidates=vector, lexical_candidates=lexical, query="ARL responsabilidades", top_k=8
    )

    assert "arl_doc" in [item.node_id for item in result]


def test_fuse_and_dedup_real_reranker_still_excludes_irrelevant_deep_lexical_hit() -> None:
    """Regression: q21 in retrieval_hybrid_live_report.md must not regress even
    with a real reranker wired -- an irrelevant lexical-only rescue candidate
    (short/low-signal text, the _StubReranker's proxy for "BGE judges this as
    unrelated") must stay excluded, same as with NoOpReranker.
    """
    vector = [
        _evidence(f"filler_{i}", text=f"relleno semantico sin relacion con mas texto numero {i}", score=0.0)
        for i in range(20)
    ]
    vector.append(_evidence("noise_doc", text="corto", score=0.0))
    lexical = [
        RetrievedEvidence(
            node_id="noise_doc",
            document_id="doc-noise_doc",
            child_chunk_id="noise_doc",
            text="corto",
            score=5.0,
            source="lexical",
            embedding_profile_id="local-bge-m3-v1",
            corpus_version="corpus-v1",
        )
    ]

    result = _service(reranker=_StubReranker())._fuse_and_dedup(
        vector_candidates=vector, lexical_candidates=lexical, query="q", top_k=8
    )

    assert "noise_doc" not in [item.node_id for item in result]
