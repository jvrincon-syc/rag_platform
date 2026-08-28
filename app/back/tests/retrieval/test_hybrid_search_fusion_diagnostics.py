from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import app.back.tests.retrieval.test_hybrid_search_fusion as hybrid_live
from retrieval.domain.models import RetrievedEvidence


def _hit(
    *,
    node_id: str,
    source: str = "vector",
    relpath: str,
    fusion_sources: list[str] | None,
    score: float = 0.9,
) -> RetrievedEvidence:
    metadata: dict[str, object] = {
        "source_relpath": relpath,
        "rag_release_id": "ragr_test",
        "dedup_dropped_count": 0,
    }
    if fusion_sources is not None:
        metadata["fusion_sources"] = fusion_sources
    return RetrievedEvidence(
        node_id=node_id,
        document_id=f"doc-{node_id}",
        parent_node_id=f"parent-{node_id}",
        child_chunk_id=node_id,
        text=f"chunk for {relpath}",
        score=score,
        source=source,  # type: ignore[arg-type]
        page_start=1,
        page_end=1,
        section_title="section",
        section_path="section/path",
        metadata=metadata,
        embedding_profile_id="local-bge-m3-v1",
        corpus_version="corpus-v1",
    )


def test_selected_question_bank_uses_focus_env_and_preserves_order(
    monkeypatch,
) -> None:
    monkeypatch.setenv(hybrid_live._FOCUS_ENV, "q15, 16, q54, q56")

    selected = hybrid_live._selected_question_bank()

    assert [number for number, _question in selected] == [15, 16, 54, 56]
    assert [question for _number, question in selected] == [
        hybrid_live.SST_E2E_QUESTIONS[14],
        hybrid_live.SST_E2E_QUESTIONS[15],
        hybrid_live.SST_E2E_QUESTIONS[53],
        hybrid_live.SST_E2E_QUESTIONS[55],
    ]


def test_collect_query_diagnostic_reports_overlap_and_lexical_rescue() -> None:
    hits = [
        _hit(
            node_id="shared-node",
            source="vector",
            relpath="docs/shared.md",
            fusion_sources=["vector", "lexical"],
        ),
        _hit(
            node_id="vector-node",
            source="vector",
            relpath="docs/vector.md",
            fusion_sources=["vector"],
        ),
        _hit(
            node_id="rescue-node",
            source="lexical",
            relpath="docs/rescue.md",
            fusion_sources=["lexical"],
        ),
    ]

    diagnostic = hybrid_live._collect_query_diagnostic(
        number=15,
        question="Que responsabilidades tiene la ARL en seguridad y salud en el trabajo?",
        hits=hits,
        vector_result={
            "candidate_count": 2,
            "top_docs": ["docs/shared.md", "docs/vector.md"],
            "node_ids": ["shared-node", "vector-node"],
        },
        lexical_result={
            "candidate_count": 2,
            "query_mode": "simple_relaxed",
            "query_modes_tried": ["spanish_strict", "simple_relaxed"],
            "top_docs": ["docs/shared.md", "docs/rescue.md"],
            "node_ids": ["shared-node", "rescue-node"],
            "top_scores": [0.82, 0.41],
            "exception": None,
        },
    )

    assert diagnostic["vector_lexical_overlap_count"] == 1
    assert diagnostic["lexical_query_mode"] == "simple_relaxed"
    assert diagnostic["lexical_hybrid_unavailable"] is False
    assert diagnostic["final_vector_lexical_count"] == 1
    assert diagnostic["final_vector_only_count"] == 1
    assert diagnostic["final_lexical_only_count"] == 1
    assert diagnostic["lexical_rescue_count"] == 1
    assert diagnostic["lexical_rescue_docs"] == ["docs/rescue.md"]


def test_write_live_report_includes_scope_smoke_and_query_diagnostics(
    tmp_path: Path,
    monkeypatch,
) -> None:
    report_path = tmp_path / "retrieval_hybrid_live_report.md"
    monkeypatch.setattr(hybrid_live, "_REPORT_PATH", report_path)

    hits = [
        _hit(
            node_id="shared-node",
            source="vector",
            relpath="docs/shared.md",
            fusion_sources=["vector", "lexical"],
        )
    ]
    diagnostic = hybrid_live._collect_query_diagnostic(
        number=15,
        question="Que responsabilidades tiene la ARL en seguridad y salud en el trabajo?",
        hits=hits,
        vector_result={
            "candidate_count": 1,
            "top_docs": ["docs/shared.md"],
            "node_ids": ["shared-node"],
        },
        lexical_result={
            "candidate_count": 1,
            "query_mode": "spanish_relaxed",
            "query_modes_tried": ["spanish_strict", "spanish_relaxed"],
            "top_docs": ["docs/shared.md"],
            "node_ids": ["shared-node"],
            "top_scores": [0.77],
            "exception": None,
        },
    )

    hybrid_live._write_live_report(
        release_id="ragr_test",
        build_attempt=1,
        profile=SimpleNamespace(
            provider="local",
            model="bge-m3",
            dimension=1024,
            distance_metric="cosine",
            normalization="l2",
        ),
        persistence={"vector_total": 353},
        indexing_target_id="target-1",
        corpus_version="corpus-v1",
        release_scope={
            "memberships": 55,
            "chunk_bundles": 55,
            "child_nodes_release": 606,
            "child_nodes_corpus": 606,
            "child_nodes_visible": 606,
        },
        smoke_results=[
            {
                "query": "ARL responsabilidades",
                "candidate_count": 1,
                "query_mode": "spanish_relaxed",
                "query_modes_tried": ["spanish_strict", "spanish_relaxed"],
                "top_docs": ["docs/shared.md"],
                "top_scores": [0.77],
                "exception": None,
            }
        ],
        query_diagnostics={15: diagnostic},
        results=[
            (
                15,
                "Que responsabilidades tiene la ARL en seguridad y salud en el trabajo?",
                hits,
            )
        ],
        documents=("docs/shared.md",),
        elapsed_seconds=12.5,
    )

    report = report_path.read_text(encoding="utf-8")

    assert "## Scope lexical release" in report
    assert "## Smoke lexical queries" in report
    assert "## Resumen hibrido diagnostico" in report
    assert "### q15. Que responsabilidades tiene la ARL" in report
    assert "vector_candidates_count" in report
    assert "ARL responsabilidades" in report
