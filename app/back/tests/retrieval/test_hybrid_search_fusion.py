"""Live hybrid retrieval: real SST corpus -> real PostgreSQL -> hybrid service.

Purpose
-------
Prove the SST hybrid question bank against REAL data while exercising the new
``RetrievalSearchService`` rules:

- real raw ingestion + normalization;
- real fresh RAG release;
- real BGE-M3 query embeddings (isolated OS worker, same as the platform E2E);
- real release-scoped pgvector candidates from PostgreSQL;
- real release-scoped PostgreSQL FTS candidates;
- real ``RetrievalSearchService`` hybrid fusion + dedup + parent diversity;
- Markdown report containing the real returned document paths and text blocks.

This is intentionally operator-run and destructive for ``proj_sst-general``.
It reuses the safety/cleanup/build helpers from
``test_end_to_end_local_platform.py`` and therefore MUST only run against the
local PostgreSQL instance accepted by that E2E's fail-closed DSN guard.

Usage
-----
    npm run python -- -m pytest \
      app/back/tests/retrieval/test_hybrid_search_fusion.py::test_live_hybrid_retrieval_question_bank \
      -v -s
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from sst_retrieval_fixture import (
    load_sst_hybrid_questions,
    sst_reusable_derived_state_exists,
)


# ---------------------------------------------------------------------------
# Repo / imports
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[4]
_BACK_SRC = _REPO_ROOT / "app" / "back" / "src"
_INDEXING_SCRIPTS = _REPO_ROOT / "scripts" / "indexing"
_E2E_PATH = (
    _REPO_ROOT
    / "app"
    / "back"
    / "tests"
    / "rag_platform"
    / "test_end_to_end_local_platform.py"
)

sys.path.insert(0, str(_BACK_SRC))
sys.path.insert(0, str(_INDEXING_SCRIPTS))

from embedding.infrastructure.postgres.repositories import (  # noqa: E402
    PostgresEmbeddingProfileRepository,
    PostgresIndexingTargetRepository,
)
from retrieval.application.retrieval_service import RetrievalSearchService  # noqa: E402
from retrieval.domain.models import RetrievalProfile, RetrievedEvidence  # noqa: E402
from retrieval.infrastructure.postgres.repositories import (  # noqa: E402
    _fts_query_modes,
    _tsquery_sql,
    _tsvector_sql,
    PostgresRetrievalProfileRepository,
)


# ---------------------------------------------------------------------------
# Identity / runtime
# ---------------------------------------------------------------------------

_PROJECT_ID = "proj_sst-general"
_PROJECT_SLUG = "sst-general"
_VARIANT_ID = "ragv_local-bge"
_EMBEDDING_PROFILE_ID = "local-bge-m3-v1"
_VECTOR_TABLE = "idx_vec_local_bge_m3_v1"
_CONSUMER_SCOPE_ID = "sst-general-live-hybrid-retrieval"
_TOP_K = 8
_REPORT_PATH = _REPO_ROOT / "retrieval_hybrid_live_report.md"

_VECTOR_TABLE_PATTERN = re.compile(r"^idx_vec_[a-z0-9_]+$")
_DISTANCE_OPERATOR = {
    "cosine": "<=>",
    "l2": "<->",
    "inner_product": "<#>",
}
_FOCUS_ENV = "RAG_PLATFORM_LIVE_RETRIEVAL_FOCUS"
_LEGACY_FOCUS_ENV = "CHATBOT_SST_LIVE_RETRIEVAL_FOCUS"
_SMOKE_QUERIES = (
    "ARL responsabilidades",
    "COPASST funciones",
    "En cuanto tiempo debe el Comite de Convivencia dar tramite a una queja?",
)


SST_E2E_QUESTIONS = load_sst_hybrid_questions()


# ---------------------------------------------------------------------------
# Reuse the proven E2E orchestration/build/BGE worker
# ---------------------------------------------------------------------------

def _load_e2e_module():
    spec = importlib.util.spec_from_file_location(
        "_hybrid_live_source_e2e",
        _E2E_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"no se pudo cargar E2E helper: {_E2E_PATH}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    e2e_questions = tuple(module._QUESTIONS)
    assert e2e_questions == SST_E2E_QUESTIONS, (
        "el banco de preguntas del live hybrid se desvio del E2E; "
        "mantener una sola matriz exacta"
    )
    return module


# ---------------------------------------------------------------------------
# DB row -> RetrievedEvidence
# ---------------------------------------------------------------------------

def _metadata_with_provenance(
    raw_metadata: object,
    *,
    source_relpath: object,
    release_id: str,
    raw_score: float,
    signal: str,
) -> dict[str, object]:
    metadata = dict(raw_metadata) if isinstance(raw_metadata, Mapping) else {}
    metadata["source_relpath"] = str(source_relpath or "")
    metadata["rag_release_id"] = release_id
    metadata[f"raw_{signal}_score"] = float(raw_score)
    return metadata


def _row_to_evidence(
    row: Sequence[object],
    *,
    source: str,
    embedding_profile_id: str,
    corpus_version: str,
    release_id: str,
) -> RetrievedEvidence:
    (
        node_id,
        document_id,
        embedding_bundle_id,
        parent_node_id,
        text,
        page_start,
        page_end,
        section_title,
        section_path,
        raw_metadata,
        source_relpath,
        score,
    ) = row

    return RetrievedEvidence(
        node_id=str(node_id),
        document_id=str(document_id),
        parent_node_id=(
            None if parent_node_id is None else str(parent_node_id)
        ),
        child_chunk_id=str(node_id),
        text=str(text or ""),
        score=float(score),
        source=source,  # type: ignore[arg-type]
        page_start=page_start,  # type: ignore[arg-type]
        page_end=page_end,  # type: ignore[arg-type]
        section_title=(
            None if section_title is None else str(section_title)
        ),
        section_path=(
            None if section_path is None else str(section_path)
        ),
        metadata=_metadata_with_provenance(
            raw_metadata,
            source_relpath=source_relpath,
            release_id=release_id,
            raw_score=float(score),
            signal=source,
        ),
        embedding_profile_id=embedding_profile_id,
        corpus_version=corpus_version,
        embedding_bundle_id=(
            None if embedding_bundle_id is None else str(embedding_bundle_id)
        ),
    )


# ---------------------------------------------------------------------------
# REAL release-scoped PostgreSQL adapters
# ---------------------------------------------------------------------------

class _ReleaseScopedVectorSearch:
    """Real pgvector adapter restricted to exactly one freshly-built release."""

    def __init__(self, connection: object, *, release_id: str) -> None:
        self._connection = connection
        self._release_id = release_id
        self.calls: list[dict[str, object]] = []
        self.last_result: dict[str, object] | None = None

    def search(
        self,
        *,
        project_id: str,
        vector_table: str,
        embedding_profile_id: str,
        indexing_target_id: str,
        corpus_version: str,
        distance_metric: str,
        query_embedding: Sequence[float],
        top_k: int,
    ) -> list[RetrievedEvidence]:
        if not _VECTOR_TABLE_PATTERN.fullmatch(vector_table):
            raise ValueError(f"vector table no permitida: {vector_table!r}")

        operator = _DISTANCE_OPERATOR[distance_metric]
        self.calls.append(
            {
                "project_id": project_id,
                "top_k": top_k,
                "vector_table": vector_table,
            }
        )

        with self._connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    v.node_id,
                    v.document_id,
                    v.embedding_bundle_id,
                    n.parent_node_id,
                    n.text,
                    n.page_start,
                    n.page_end,
                    COALESCE(n.section_title, p.section_title) AS section_title,
                    COALESCE(n.section_path, p.section_path) AS section_path,
                    n.metadata,
                    n.source_relpath,
                    1 - (v.embedding {operator} %s::vector) AS score
                FROM {vector_table} AS v
                JOIN indexing_nodes AS n
                  ON n.project_id = v.project_id
                 AND n.node_id = v.node_id
                LEFT JOIN indexing_nodes AS p
                  ON p.project_id = n.project_id
                 AND p.node_id = n.parent_node_id
                WHERE v.project_id = %s
                  AND v.embedding_profile_id = %s
                  AND v.indexing_target_id = %s
                  AND v.corpus_version = %s
                  AND EXISTS (
                      SELECT 1
                      FROM rag_release_memberships AS m
                      WHERE m.rag_release_id = %s
                        AND m.project_id = v.project_id
                        AND m.embedding_bundle_id = v.embedding_bundle_id
                  )
                ORDER BY v.embedding {operator} %s::vector
                LIMIT %s
                """,
                (
                    list(query_embedding),
                    project_id,
                    embedding_profile_id,
                    indexing_target_id,
                    corpus_version,
                    self._release_id,
                    list(query_embedding),
                    top_k,
                ),
            )
            rows = list(cursor.fetchall())

        evidence = [
            _row_to_evidence(
                row,
                source="vector",
                embedding_profile_id=embedding_profile_id,
                corpus_version=corpus_version,
                release_id=self._release_id,
            )
            for row in rows
        ]
        self.last_result = {
            "candidate_count": len(evidence),
            "top_docs": [
                str((item.metadata or {}).get("source_relpath", ""))
                for item in evidence[:5]
            ],
            "node_ids": [item.node_id for item in evidence],
        }
        return evidence


class _ReleaseScopedLexicalSearch:
    """Real PostgreSQL Spanish FTS restricted to the release's chunk bundles."""

    def __init__(self, connection: object, *, release_id: str) -> None:
        self._connection = connection
        self._release_id = release_id
        self.calls: list[dict[str, object]] = []
        self.last_result: dict[str, object] | None = None

    def search(
        self,
        *,
        project_id: str,
        query: str,
        embedding_profile_id: str,
        corpus_version: str,
        top_k: int,
    ) -> list[RetrievedEvidence]:
        attempted_modes: list[str] = []

        with self._connection.cursor() as cursor:
            try:
                for mode in _fts_query_modes(query):
                    attempted_modes.append(mode.mode_name)
                    tsvector = _tsvector_sql("n", config=mode.config)
                    tsquery = _tsquery_sql(mode)
                    cursor.execute(
                        f"""
                        SELECT
                            n.node_id,
                            n.document_id,
                            NULL AS embedding_bundle_id,
                            n.parent_node_id,
                            n.text,
                            n.page_start,
                            n.page_end,
                            COALESCE(n.section_title, p.section_title) AS section_title,
                            COALESCE(n.section_path, p.section_path) AS section_path,
                            n.metadata,
                            n.source_relpath,
                            ts_rank_cd(
                                {tsvector},
                                {tsquery}
                            ) AS score
                        FROM indexing_nodes AS n
                        LEFT JOIN indexing_nodes AS p
                          ON p.project_id = n.project_id
                         AND p.node_id = n.parent_node_id
                        WHERE n.project_id = %s
                          AND n.node_role = 'child'
                          AND n.corpus_version = %s
                          AND EXISTS (
                              SELECT 1
                              FROM rag_release_memberships AS m
                              WHERE m.rag_release_id = %s
                                AND m.project_id = n.project_id
                                AND m.chunk_bundle_id = n.source_chunk_bundle_id
                          )
                          AND ({tsvector}) @@ {tsquery}
                        ORDER BY score DESC
                        LIMIT %s
                        """,
                        (
                            mode.query_text,
                            project_id,
                            corpus_version,
                            self._release_id,
                            mode.query_text,
                            top_k,
                        ),
                    )
                    rows = list(cursor.fetchall())
                    if not rows:
                        continue
                    evidence: list[RetrievedEvidence] = []
                    for row in rows:
                        item = _row_to_evidence(
                            row,
                            source="lexical",
                            embedding_profile_id=embedding_profile_id,
                            corpus_version=corpus_version,
                            release_id=self._release_id,
                        )
                        evidence.append(
                            item.model_copy(
                                update={
                                    "metadata": {
                                        **item.metadata,
                                        "fts_query_mode": mode.mode_name,
                                    }
                                }
                            )
                        )
                    self.last_result = {
                        "query": query,
                        "query_mode": mode.mode_name,
                        "query_modes_tried": list(attempted_modes),
                        "candidate_count": len(evidence),
                        "top_docs": [
                            str((item.metadata or {}).get("source_relpath", ""))
                            for item in evidence[:5]
                        ],
                        "top_scores": [float(item.score) for item in evidence[:5]],
                        "node_ids": [item.node_id for item in evidence],
                        "exception": None,
                    }
                    self.calls.append(dict(self.last_result))
                    return evidence
            except Exception as error:  # noqa: BLE001
                self.last_result = {
                    "query": query,
                    "query_mode": attempted_modes[-1] if attempted_modes else None,
                    "query_modes_tried": list(attempted_modes),
                    "candidate_count": 0,
                    "top_docs": [],
                    "top_scores": [],
                    "node_ids": [],
                    "exception": repr(error),
                }
                self.calls.append(dict(self.last_result))
                raise

        self.last_result = {
            "query": query,
            "query_mode": attempted_modes[-1] if attempted_modes else None,
            "query_modes_tried": list(attempted_modes),
            "candidate_count": 0,
            "top_docs": [],
            "top_scores": [],
            "node_ids": [],
            "exception": None,
        }
        self.calls.append(dict(self.last_result))
        return []


class _ReleaseScopedParentExpansion:
    """Real parent lookup, also limited to source chunk bundles in the release."""

    def __init__(self, connection: object, *, release_id: str) -> None:
        self._connection = connection
        self._release_id = release_id

    def expand(
        self,
        *,
        project_id: str,
        parent_node_ids: Sequence[str],
        embedding_profile_id: str,
        corpus_version: str,
    ) -> dict[str, RetrievedEvidence]:
        if not parent_node_ids:
            return {}

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    n.node_id,
                    n.document_id,
                    NULL AS embedding_bundle_id,
                    n.parent_node_id,
                    n.text,
                    n.page_start,
                    n.page_end,
                    n.section_title,
                    n.section_path,
                    n.metadata,
                    n.source_relpath,
                    0.0 AS score
                FROM indexing_nodes AS n
                WHERE n.project_id = %s
                  AND n.node_id = ANY(%s)
                  AND n.node_role = 'parent'
                  AND n.corpus_version = %s
                  AND EXISTS (
                      SELECT 1
                      FROM rag_release_memberships AS m
                      WHERE m.rag_release_id = %s
                        AND m.project_id = n.project_id
                        AND m.chunk_bundle_id = n.source_chunk_bundle_id
                  )
                """,
                (
                    project_id,
                    list(dict.fromkeys(parent_node_ids)),
                    corpus_version,
                    self._release_id,
                ),
            )
            rows = list(cursor.fetchall())

        evidence = [
            _row_to_evidence(
                row,
                source="lexical",
                embedding_profile_id=embedding_profile_id,
                corpus_version=corpus_version,
                release_id=self._release_id,
            )
            for row in rows
        ]
        return {item.node_id: item for item in evidence}


# ---------------------------------------------------------------------------
# Real BGE vectors, injected into RetrievalSearchService without loading Torch
# in the pytest process. The vectors themselves come from the E2E's real worker.
# ---------------------------------------------------------------------------

class _PrecomputedRealQueryEmbedding:
    def __init__(
        self,
        *,
        embedding_profile: object,
        vectors_by_query: Mapping[str, Sequence[float]],
    ) -> None:
        self._embedding_profile = embedding_profile
        self._vectors_by_query = {
            query: list(vector)
            for query, vector in vectors_by_query.items()
        }
        self.queries: list[str] = []

    def resolve_profile(self, retrieval_profile: RetrievalProfile):
        assert retrieval_profile.embedding_profile_id == _EMBEDDING_PROFILE_ID
        return self._embedding_profile

    def embed_queries(self, *, retrieval_profile, queries):
        self.queries.extend(str(query) for query in queries)
        return [
            SimpleNamespace(vector=self._vectors_by_query[str(query)])
            for query in queries
        ]


# ---------------------------------------------------------------------------
# Release lane discovery
# ---------------------------------------------------------------------------

def _release_lane(
    connection: object,
    *,
    release_id: str,
) -> tuple[str, str]:
    """Return the single indexing_target_id + corpus_version used by the release."""

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT DISTINCT v.indexing_target_id, v.corpus_version
            FROM {_VECTOR_TABLE} AS v
            WHERE v.project_id = %s
              AND EXISTS (
                  SELECT 1
                  FROM rag_release_memberships AS m
                  WHERE m.rag_release_id = %s
                    AND m.project_id = v.project_id
                    AND m.embedding_bundle_id = v.embedding_bundle_id
              )
            ORDER BY v.indexing_target_id, v.corpus_version
            """,
            (_PROJECT_ID, release_id),
        )
        rows = list(cursor.fetchall())

    assert len(rows) == 1, (
        f"release {release_id} debe resolver exactamente una lane; rows={rows!r}"
    )
    indexing_target_id, corpus_version = rows[0]
    return str(indexing_target_id), str(corpus_version)


def _selected_question_bank() -> list[tuple[int, str]]:
    focus = os.environ.get(_FOCUS_ENV, "").strip() or os.environ.get(
        _LEGACY_FOCUS_ENV, ""
    ).strip()
    all_questions = list(enumerate(SST_E2E_QUESTIONS, start=1))
    if not focus:
        return all_questions

    selected_numbers: list[int] = []
    for raw_token in focus.split(","):
        token = raw_token.strip().casefold()
        if not token:
            continue
        if token.startswith("q"):
            token = token[1:]
        try:
            number = int(token)
        except ValueError:
            continue
        if 1 <= number <= len(SST_E2E_QUESTIONS) and number not in selected_numbers:
            selected_numbers.append(number)

    if not selected_numbers:
        raise ValueError(
            f"{_FOCUS_ENV} debe contener numeros de preguntas, por ejemplo q15,q16,q54,q56"
        )

    return [
        (number, SST_E2E_QUESTIONS[number - 1])
        for number in selected_numbers
    ]


def _release_lexical_scope_facts(
    connection: object,
    *,
    release_id: str,
    corpus_version: str,
) -> dict[str, int]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(*) FROM rag_release_memberships
             WHERE rag_release_id = %s
               AND project_id = %s
            """,
            (release_id, _PROJECT_ID),
        )
        memberships = int(cursor.fetchone()[0])

        cursor.execute(
            """
            SELECT count(DISTINCT chunk_bundle_id) FROM rag_release_memberships
             WHERE rag_release_id = %s
               AND project_id = %s
            """,
            (release_id, _PROJECT_ID),
        )
        chunk_bundles = int(cursor.fetchone()[0])

        cursor.execute(
            """
            SELECT count(*) FROM indexing_nodes AS n
             WHERE n.project_id = %s
               AND n.node_role = 'child'
               AND EXISTS (
                   SELECT 1
                   FROM rag_release_memberships AS m
                   WHERE m.rag_release_id = %s
                     AND m.project_id = n.project_id
                     AND m.chunk_bundle_id = n.source_chunk_bundle_id
               )
            """,
            (_PROJECT_ID, release_id),
        )
        child_nodes_release = int(cursor.fetchone()[0])

        cursor.execute(
            """
            SELECT count(*) FROM indexing_nodes AS n
             WHERE n.project_id = %s
               AND n.node_role = 'child'
               AND n.corpus_version = %s
               AND EXISTS (
                   SELECT 1
                   FROM rag_release_memberships AS m
                   WHERE m.rag_release_id = %s
                     AND m.project_id = n.project_id
                     AND m.chunk_bundle_id = n.source_chunk_bundle_id
               )
            """,
            (_PROJECT_ID, corpus_version, release_id),
        )
        child_nodes_corpus = int(cursor.fetchone()[0])

        cursor.execute(
            """
            SELECT count(*) FROM indexing_nodes AS n
             JOIN indexing_normalized_documents AS d
               ON d.document_id = n.document_id
            WHERE n.project_id = %s
              AND n.node_role = 'child'
              AND n.corpus_version = %s
              AND d.processing_status = 'processed'
              AND d.review_status = 'approved'
              AND EXISTS (
                  SELECT 1
                  FROM rag_release_memberships AS m
                  WHERE m.rag_release_id = %s
                    AND m.project_id = n.project_id
                    AND m.chunk_bundle_id = n.source_chunk_bundle_id
              )
            """,
            (_PROJECT_ID, corpus_version, release_id),
        )
        child_nodes_visible = int(cursor.fetchone()[0])

    return {
        "memberships": memberships,
        "chunk_bundles": chunk_bundles,
        "child_nodes_release": child_nodes_release,
        "child_nodes_corpus": child_nodes_corpus,
        "child_nodes_visible": child_nodes_visible,
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _md(value: object) -> str:
    return (
        str(value or "")
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def _hit_source_set(hit: RetrievedEvidence) -> set[str]:
    metadata = dict(hit.metadata or {})
    sources = metadata.get("fusion_sources", [])
    if isinstance(sources, (list, tuple, set)):
        source_set = {str(value) for value in sources if str(value)}
    else:
        source_set = {str(sources)} if sources else set()
    if not source_set:
        source_set.add(str(hit.source))
    return source_set


def _hit_relpath(hit: RetrievedEvidence) -> str:
    return str((hit.metadata or {}).get("source_relpath", ""))


def _final_source_counts(
    hits: Sequence[RetrievedEvidence],
) -> tuple[int, int, int, int]:
    fused_count = 0
    lexical_only_count = 0
    vector_only_count = 0
    dedup_dropped = 0

    for hit in hits:
        source_set = _hit_source_set(hit)
        if {"vector", "lexical"} <= source_set:
            fused_count += 1
        elif "lexical" in source_set:
            lexical_only_count += 1
        elif "vector" in source_set:
            vector_only_count += 1
        dedup_dropped += int((hit.metadata or {}).get("dedup_dropped_count", 0) or 0)

    return fused_count, lexical_only_count, vector_only_count, dedup_dropped


def _collect_query_diagnostic(
    *,
    number: int,
    question: str,
    hits: Sequence[RetrievedEvidence],
    vector_result: Mapping[str, object] | None,
    lexical_result: Mapping[str, object] | None,
) -> dict[str, object]:
    vector_payload = dict(vector_result or {})
    lexical_payload = dict(lexical_result or {})

    vector_docs = [
        str(doc)
        for doc in vector_payload.get("top_docs", [])
        if str(doc)
    ]
    lexical_docs = [
        str(doc)
        for doc in lexical_payload.get("top_docs", [])
        if str(doc)
    ]
    vector_node_ids = {
        str(node_id)
        for node_id in vector_payload.get("node_ids", [])
        if str(node_id)
    }
    lexical_node_ids = {
        str(node_id)
        for node_id in lexical_payload.get("node_ids", [])
        if str(node_id)
    }

    fused_count, lexical_only_count, vector_only_count, _dedup = _final_source_counts(
        hits
    )
    raw_vector_doc_set = set(vector_docs)
    lexical_rescue_docs: list[str] = []
    for hit in hits:
        source_set = _hit_source_set(hit)
        relpath = _hit_relpath(hit)
        if (
            "lexical" in source_set
            and relpath
            and relpath not in raw_vector_doc_set
            and relpath not in lexical_rescue_docs
        ):
            lexical_rescue_docs.append(relpath)

    lexical_exception = lexical_payload.get("exception")
    lexical_hybrid_unavailable = bool(lexical_exception) or any(
        str((hit.metadata or {}).get("degraded_reason", ""))
        == "lexical_hybrid_unavailable"
        or str((hit.metadata or {}).get("retrieval_mode", ""))
        == "vector_only_degraded"
        for hit in hits
    )

    return {
        "question_number": number,
        "question": question,
        "vector_candidates_count": int(vector_payload.get("candidate_count", 0) or 0),
        "lexical_candidates_count": int(
            lexical_payload.get("candidate_count", 0) or 0
        ),
        "vector_lexical_overlap_count": len(vector_node_ids & lexical_node_ids),
        "lexical_query_mode": lexical_payload.get("query_mode"),
        "lexical_query_modes_tried": list(
            lexical_payload.get("query_modes_tried", []) or []
        ),
        "lexical_exception": lexical_exception,
        "lexical_hybrid_unavailable": lexical_hybrid_unavailable,
        "top_vector_docs": vector_docs,
        "top_lexical_docs": lexical_docs,
        "top_lexical_scores": [
            float(score)
            for score in lexical_payload.get("top_scores", [])
        ],
        "final_vector_lexical_count": fused_count,
        "final_vector_only_count": vector_only_count,
        "final_lexical_only_count": lexical_only_count,
        "lexical_rescue_count": len(lexical_rescue_docs),
        "lexical_rescue_docs": lexical_rescue_docs,
    }


def _summarize_query_diagnostics(
    query_diagnostics: Mapping[int, Mapping[str, object]],
) -> dict[str, int]:
    summary = {
        "questions_total": len(query_diagnostics),
        "queries_with_vector_candidates": 0,
        "queries_with_lexical_candidates": 0,
        "queries_without_lexical_candidates": 0,
        "raw_vector_candidates_total": 0,
        "raw_lexical_candidates_total": 0,
        "raw_vector_lexical_overlap_total": 0,
        "lexical_hybrid_failures": 0,
        "final_vector_lexical_hits": 0,
        "final_vector_only_hits": 0,
        "final_lexical_only_hits": 0,
        "lexical_rescue_count": 0,
    }

    for diagnostic in query_diagnostics.values():
        vector_count = int(diagnostic.get("vector_candidates_count", 0) or 0)
        lexical_count = int(diagnostic.get("lexical_candidates_count", 0) or 0)
        summary["raw_vector_candidates_total"] += vector_count
        summary["raw_lexical_candidates_total"] += lexical_count
        summary["raw_vector_lexical_overlap_total"] += int(
            diagnostic.get("vector_lexical_overlap_count", 0) or 0
        )
        summary["final_vector_lexical_hits"] += int(
            diagnostic.get("final_vector_lexical_count", 0) or 0
        )
        summary["final_vector_only_hits"] += int(
            diagnostic.get("final_vector_only_count", 0) or 0
        )
        summary["final_lexical_only_hits"] += int(
            diagnostic.get("final_lexical_only_count", 0) or 0
        )
        summary["lexical_rescue_count"] += int(
            diagnostic.get("lexical_rescue_count", 0) or 0
        )
        if vector_count > 0:
            summary["queries_with_vector_candidates"] += 1
        if lexical_count > 0:
            summary["queries_with_lexical_candidates"] += 1
        else:
            summary["queries_without_lexical_candidates"] += 1
        if diagnostic.get("lexical_hybrid_unavailable"):
            summary["lexical_hybrid_failures"] += 1

    return summary


def _write_live_report_legacy(
    *,
    release_id: str,
    build_attempt: int,
    profile: object,
    persistence: Mapping[str, object],
    indexing_target_id: str,
    corpus_version: str,
    results: list[tuple[str, list[RetrievedEvidence]]],
    documents: Sequence[str],
    elapsed_seconds: float,
) -> None:
    fused_count = 0
    lexical_only_count = 0
    vector_only_count = 0
    dedup_dropped = 0

    for _question, hits in results:
        for hit in hits:
            metadata = dict(hit.metadata or {})
            sources = metadata.get("fusion_sources", [])
            if isinstance(sources, (list, tuple, set)):
                source_set = {str(value) for value in sources}
            else:
                source_set = {str(sources)} if sources else {hit.source}

            if {"vector", "lexical"} <= source_set:
                fused_count += 1
            elif "lexical" in source_set:
                lexical_only_count += 1
            elif "vector" in source_set:
                vector_only_count += 1

            dedup_dropped += int(metadata.get("dedup_dropped_count", 0) or 0)

    lines: list[str] = [
        "# Reporte retrieval híbrido LIVE (PostgreSQL + BGE-M3)",
        "",
        f"- Generado: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Proyecto: `{_PROJECT_ID}`",
        f"- Variante: `{_VARIANT_ID}`",
        f"- Release: `{release_id}`",
        f"- Build attempt: `{build_attempt}`",
        f"- Documentos: `{len(documents)}`",
        f"- Vectores release-scoped: `{persistence['vector_total']}`",
        f"- Indexing target: `{indexing_target_id}`",
        f"- Corpus version: `{corpus_version}`",
        f"- Preguntas: `{len(results)}`",
        f"- Top-k final: `{_TOP_K}`",
        f"- Tiempo total: `{elapsed_seconds:.1f}s`",
        "",
        "## Embedding recipe",
        "",
        f"- provider: `{profile.provider}`",
        f"- model: `{profile.model}`",
        f"- dimension: `{profile.dimension}`",
        f"- metric: `{profile.distance_metric}`",
        f"- normalization: `{profile.normalization}`",
        f"- profile: `{_EMBEDDING_PROFILE_ID}`",
        "",
        "## Resumen híbrido",
        "",
        f"- hits fusionados vector+lexical: `{fused_count}`",
        f"- hits lexical-only: `{lexical_only_count}`",
        f"- hits vector-only: `{vector_only_count}`",
        f"- candidatos descartados por dedup: `{dedup_dropped}`",
        "",
        f"## Retrieval - {len(results)} preguntas, top_k={_TOP_K}",
        "",
    ]

    for number, (question, hits) in enumerate(results, start=1):
        lines.extend(
            [
                f"### q{number:02d}. {question}",
                "",
                (
                    "| # | score | documento | source | fusion_sources | "
                    "parent | seccion | ruta_seccion | paginas | dedup | chunk |"
                ),
                (
                    "|---:|------:|-----------|--------|----------------|"
                    "--------|---------|--------------|---------|------:|-------|"
                ),
            ]
        )

        if not hits:
            lines.append("| - | - | _sin hits_ | - | - | - | - | - | - | - | - |")
            lines.append("")
            continue

        for rank, hit in enumerate(hits, start=1):
            metadata = dict(hit.metadata or {})
            fusion = metadata.get("fusion_sources", [hit.source])
            if isinstance(fusion, (list, tuple, set)):
                fusion_text = ", ".join(str(v) for v in fusion)
            else:
                fusion_text = str(fusion)

            pages = ""
            if hit.page_start is not None or hit.page_end is not None:
                pages = f"{hit.page_start or ''}-{hit.page_end or ''}"

            # 3000, no 1200: un child chunk real (child_max_tokens) puede pasar de
            # 1200 chars y cortar justo antes del dato que responde la pregunta
            # (visto en vivo: q23 cortaba "nombro como presidente" antes de decir
            # a quien -- el chunk real SI tenia el nombre completo, el reporte
            # mentia por truncar la vista, no la recuperacion).
            snippet = _md(hit.text)[:3000]

            lines.append(
                f"| {rank} | {float(hit.score):.6f} | "
                f"{_md(metadata.get('source_relpath', ''))} | "
                f"{_md(hit.source)} | "
                f"{_md(fusion_text)} | "
                f"{_md(hit.parent_node_id or '')} | "
                f"{_md(hit.section_title or '')} | "
                f"{_md(hit.section_path or '')} | "
                f"{_md(pages)} | "
                f"{int(metadata.get('dedup_dropped_count', 0) or 0)} | "
                f"{snippet} |"
            )

        lines.append("")

    lines.extend(["## Documentos incluidos", ""])
    for relpath in documents:
        lines.append(f"- `{relpath}`")
    lines.append("")

    _REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def _write_live_report(
    *,
    release_id: str,
    build_attempt: int,
    profile: object,
    persistence: Mapping[str, object],
    indexing_target_id: str,
    corpus_version: str,
    release_scope: Mapping[str, int],
    smoke_results: Sequence[Mapping[str, object]],
    query_diagnostics: Mapping[int, Mapping[str, object]],
    results: list[tuple[int, str, list[RetrievedEvidence]]],
    documents: Sequence[str],
    elapsed_seconds: float,
) -> None:
    summary = _summarize_query_diagnostics(query_diagnostics)
    dedup_dropped = sum(
        _final_source_counts(hits)[3]
        for _number, _question, hits in results
    )

    lines: list[str] = [
        "# Reporte retrieval hibrido LIVE (PostgreSQL + BGE-M3)",
        "",
        f"- Generado: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Proyecto: `{_PROJECT_ID}`",
        f"- Variante: `{_VARIANT_ID}`",
        f"- Release: `{release_id}`",
        f"- Build attempt: `{build_attempt}`",
        f"- Documentos: `{len(documents)}`",
        f"- Vectores release-scoped: `{persistence['vector_total']}`",
        f"- Indexing target: `{indexing_target_id}`",
        f"- Corpus version: `{corpus_version}`",
        f"- Preguntas: `{len(results)}`",
        f"- Banco total SST: `{len(SST_E2E_QUESTIONS)}`",
        f"- Top-k final: `{_TOP_K}`",
        f"- Tiempo total: `{elapsed_seconds:.1f}s`",
        "",
        "## Embedding recipe",
        "",
        f"- provider: `{profile.provider}`",
        f"- model: `{profile.model}`",
        f"- dimension: `{profile.dimension}`",
        f"- metric: `{profile.distance_metric}`",
        f"- normalization: `{profile.normalization}`",
        f"- profile: `{_EMBEDDING_PROFILE_ID}`",
        "",
        "## Scope lexical release",
        "",
        f"- release memberships: `{release_scope.get('memberships', 0)}`",
        f"- release chunk bundles: `{release_scope.get('chunk_bundles', 0)}`",
        f"- child nodes release scoped: `{release_scope.get('child_nodes_release', 0)}`",
        f"- child nodes corpus scoped: `{release_scope.get('child_nodes_corpus', 0)}`",
        f"- child nodes lexical visible: `{release_scope.get('child_nodes_visible', 0)}`",
        "",
        "## Smoke lexical queries",
        "",
    ]

    if not smoke_results:
        lines.append("- _sin smoke queries_")
        lines.append("")
    else:
        lines.extend(
            [
                "| query | candidates | mode | modes_tried | top_docs | top_scores | exception |",
                "|-------|-----------:|------|-------------|----------|------------|-----------|",
            ]
        )
        for result in smoke_results:
            top_docs = ", ".join(str(value) for value in result.get("top_docs", []))
            top_scores = ", ".join(
                f"{float(score):.4f}" for score in result.get("top_scores", [])
            )
            modes_tried = ", ".join(
                str(value) for value in result.get("query_modes_tried", [])
            )
            lines.append(
                f"| {_md(result.get('query', ''))} | "
                f"{int(result.get('candidate_count', 0) or 0)} | "
                f"{_md(result.get('query_mode', ''))} | "
                f"{_md(modes_tried)} | "
                f"{_md(top_docs)} | "
                f"{_md(top_scores)} | "
                f"{_md(result.get('exception', ''))} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Resumen hibrido diagnostico",
            "",
            f"- questions_total: `{summary['questions_total']}`",
            f"- queries_with_vector_candidates: `{summary['queries_with_vector_candidates']}`",
            f"- queries_with_lexical_candidates: `{summary['queries_with_lexical_candidates']}`",
            f"- queries_without_lexical_candidates: `{summary['queries_without_lexical_candidates']}`",
            f"- raw_vector_candidates_total: `{summary['raw_vector_candidates_total']}`",
            f"- raw_lexical_candidates_total: `{summary['raw_lexical_candidates_total']}`",
            f"- raw_vector_lexical_overlap_total: `{summary['raw_vector_lexical_overlap_total']}`",
            f"- lexical_hybrid_failures: `{summary['lexical_hybrid_failures']}`",
            f"- final_vector_lexical_hits: `{summary['final_vector_lexical_hits']}`",
            f"- final_vector_only_hits: `{summary['final_vector_only_hits']}`",
            f"- final_lexical_only_hits: `{summary['final_lexical_only_hits']}`",
            f"- lexical_rescue_count: `{summary['lexical_rescue_count']}`",
            f"- candidatos_descartados_por_dedup: `{dedup_dropped}`",
            "",
            f"## Retrieval - {len(results)} preguntas, top_k={_TOP_K}",
            "",
        ]
    )

    for number, question, hits in results:
        diagnostic = dict(query_diagnostics.get(number, {}))
        top_vector_docs = ", ".join(
            str(value) for value in diagnostic.get("top_vector_docs", [])
        )
        top_lexical_docs = ", ".join(
            str(value) for value in diagnostic.get("top_lexical_docs", [])
        )
        lexical_rescue_docs = ", ".join(
            str(value) for value in diagnostic.get("lexical_rescue_docs", [])
        )
        lexical_modes_tried = ", ".join(
            str(value) for value in diagnostic.get("lexical_query_modes_tried", [])
        )

        lines.extend(
            [
                f"### q{number:02d}. {question}",
                "",
                f"- vector_candidates_count: `{int(diagnostic.get('vector_candidates_count', 0) or 0)}`",
                f"- lexical_candidates_count: `{int(diagnostic.get('lexical_candidates_count', 0) or 0)}`",
                f"- vector_lexical_overlap_count: `{int(diagnostic.get('vector_lexical_overlap_count', 0) or 0)}`",
                f"- lexical_query_mode: `{_md(diagnostic.get('lexical_query_mode', ''))}`",
                f"- lexical_query_modes_tried: `{_md(lexical_modes_tried)}`",
                f"- lexical_hybrid_unavailable: `{bool(diagnostic.get('lexical_hybrid_unavailable', False))}`",
                f"- lexical_exception: `{_md(diagnostic.get('lexical_exception', ''))}`",
                f"- final_vector_lexical_count: `{int(diagnostic.get('final_vector_lexical_count', 0) or 0)}`",
                f"- final_vector_only_count: `{int(diagnostic.get('final_vector_only_count', 0) or 0)}`",
                f"- final_lexical_only_count: `{int(diagnostic.get('final_lexical_only_count', 0) or 0)}`",
                f"- lexical_rescue_count: `{int(diagnostic.get('lexical_rescue_count', 0) or 0)}`",
                f"- top_vector_docs: `{_md(top_vector_docs)}`",
                f"- top_lexical_docs: `{_md(top_lexical_docs)}`",
                f"- lexical_rescue_docs: `{_md(lexical_rescue_docs)}`",
                "",
                (
                    "| # | score | documento | source | fusion_sources | "
                    "parent | seccion | ruta_seccion | paginas | dedup | chunk |"
                ),
                (
                    "|---:|------:|-----------|--------|----------------|"
                    "--------|---------|--------------|---------|------:|-------|"
                ),
            ]
        )

        if not hits:
            lines.append("| - | - | _sin hits_ | - | - | - | - | - | - | - | - |")
            lines.append("")
            continue

        for rank, hit in enumerate(hits, start=1):
            metadata = dict(hit.metadata or {})
            pages = ""
            if hit.page_start is not None or hit.page_end is not None:
                pages = f"{hit.page_start or ''}-{hit.page_end or ''}"

            lines.append(
                f"| {rank} | {float(hit.score):.6f} | "
                f"{_md(metadata.get('source_relpath', ''))} | "
                f"{_md(hit.source)} | "
                f"{_md(', '.join(sorted(_hit_source_set(hit))))} | "
                f"{_md(hit.parent_node_id or '')} | "
                f"{_md(hit.section_title or '')} | "
                f"{_md(hit.section_path or '')} | "
                f"{_md(pages)} | "
                f"{int(metadata.get('dedup_dropped_count', 0) or 0)} | "
                f"{_md(hit.text)[:1200]} |"
            )

        lines.append("")

    lines.extend(["## Documentos incluidos", ""])
    for relpath in documents:
        lines.append(f"- `{relpath}`")
    lines.append("")

    _REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Assertions over REAL retrieval results
# ---------------------------------------------------------------------------

def _canonical_text(text: str) -> str:
    return " ".join(text.casefold().split())


def _assert_real_result_rules(
    *,
    number: int,
    question: str,
    hits: Sequence[RetrievedEvidence],
    release_id: str,
) -> None:
    assert hits, f"q{number:02d}: sin hits reales para {question!r}"
    assert len(hits) <= _TOP_K

    node_ids = [hit.node_id for hit in hits]
    assert len(node_ids) == len(set(node_ids)), (
        f"q{number:02d}: node_id duplicado"
    )

    canonical = [_canonical_text(hit.text) for hit in hits]
    assert len(canonical) == len(set(canonical)), (
        f"q{number:02d}: contenido duplicado sobrevivio al dedup"
    )

    parent_counts: dict[str, int] = {}
    for hit in hits:
        metadata = dict(hit.metadata or {})
        assert metadata.get("rag_release_id") == release_id
        if hit.parent_node_id:
            parent_counts[hit.parent_node_id] = (
                parent_counts.get(hit.parent_node_id, 0) + 1
            )

    assert all(count <= 2 for count in parent_counts.values()), (
        f"q{number:02d}: un parent ocupa mas de 2 slots: {parent_counts}"
    )


def _assert_q01_native_policy_source(
    hits: Sequence[RetrievedEvidence],
) -> None:
    paths = [
        str((hit.metadata or {}).get("source_relpath", ""))
        for hit in hits
    ]
    assert any(path.endswith("manuales/politica/politica.md") for path in paths), (
        "q01: la politica nativa .md debe sobrevivir en el top-k real"
    )


def _assert_q15_arl_lexical_rescue(
    hits: Sequence[RetrievedEvidence],
) -> None:
    paths = [
        str((hit.metadata or {}).get("source_relpath", ""))
        for hit in hits
    ]
    assert any(
        path.endswith(
            "manuales/organizacion/arl/funciones_responsabilidades.md"
        )
        for path in paths
    ), (
        "q15: el híbrido real debe rescatar "
        "arl/funciones_responsabilidades.md dentro del top-k"
    )


@dataclass(frozen=True)
class _ReusableReleaseState:
    revisions: tuple[tuple[str, str], ...]
    revision_relpaths: tuple[str, ...]
    release_id: str
    corpus_snapshot_id: str
    build_attempt: int
    built_stages: int
    reused_stages: int


def _should_preserve_live_state_after_test(
    *,
    force_clean: bool,
    reusable_state_is_valid: bool,
) -> bool:
    del force_clean, reusable_state_is_valid
    return True


def _find_reusable_release_state(
    e2e: object,
    *,
    dsn: str,
    revisions: Sequence[tuple[str, str]],
) -> _ReusableReleaseState | None:
    revision_ids = [revision_id for _relpath, revision_id in revisions]
    if not revision_ids:
        return None

    connection = e2e._connect(dsn)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    r.rag_release_id,
                    r.corpus_snapshot_id,
                    COALESCE(j.built_stages, 0) AS built_stages,
                    COALESCE(j.reused_stages, 0) AS reused_stages
                FROM rag_releases AS r
                JOIN rag_release_memberships AS m
                  ON m.rag_release_id = r.rag_release_id
                LEFT JOIN LATERAL (
                    SELECT built_stages, reused_stages
                    FROM release_build_jobs
                    WHERE rag_release_id = r.rag_release_id
                      AND state = 'completed'
                    ORDER BY created_at DESC, build_job_id DESC
                    LIMIT 1
                ) AS j ON TRUE
                WHERE r.project_id = %s
                  AND EXISTS (
                      SELECT 1
                      FROM {_VECTOR_TABLE} AS v
                      WHERE v.project_id = r.project_id
                        AND EXISTS (
                            SELECT 1
                            FROM rag_release_memberships AS rm
                            WHERE rm.rag_release_id = r.rag_release_id
                              AND rm.project_id = v.project_id
                              AND rm.embedding_bundle_id = v.embedding_bundle_id
                        )
                  )
                GROUP BY
                    r.rag_release_id,
                    r.corpus_snapshot_id,
                    r.created_at,
                    j.built_stages,
                    j.reused_stages
                HAVING count(DISTINCT m.source_document_revision_id) = %s
                   AND bool_and(m.source_document_revision_id = ANY(%s))
                ORDER BY r.created_at DESC, r.rag_release_id DESC
                LIMIT 1
                """,
                (
                    _PROJECT_ID,
                    len(revision_ids),
                    revision_ids,
                ),
            )
            row = cursor.fetchone()
    finally:
        connection.close()

    if row is None:
        return None

    return _ReusableReleaseState(
        revisions=tuple((relpath, revision_id) for relpath, revision_id in revisions),
        revision_relpaths=tuple(relpath for relpath, _revision_id in revisions),
        release_id=str(row[0]),
        corpus_snapshot_id=str(row[1]),
        build_attempt=0,
        built_stages=int(row[2] or 0),
        reused_stages=int(row[3] or 0),
    )


def _reusable_live_state(
    e2e: object,
    *,
    dsn: str,
    raw_relpaths: Sequence[str],
) -> _ReusableReleaseState | None:
    if not sst_reusable_derived_state_exists(e2e._PROJECT_ROOT):
        return None

    revisions = tuple(e2e._source_revisions_for_project(dsn))
    if not revisions:
        return None

    revision_relpaths = tuple(relpath for relpath, _ in revisions)
    if set(revision_relpaths) != set(raw_relpaths):
        return None

    return _find_reusable_release_state(
        e2e,
        dsn=dsn,
        revisions=revisions,
    )


def _build_release_with_optional_reuse(
    e2e: object,
    *,
    dsn: str,
    revisions: tuple[tuple[str, str], ...],
    progress: object,
    reusable_release: _ReusableReleaseState | None,
):
    if reusable_release is None:
        return e2e._build_fresh_release_with_native_retry(
            dsn,
            revisions=revisions,
            progress=progress,
        )

    progress.detail(
        "reusing existing release without creating a new build: "
        f"release={reusable_release.release_id}"
    )
    snapshot = SimpleNamespace(
        corpus_snapshot_id=SimpleNamespace(value=reusable_release.corpus_snapshot_id)
    )
    release = SimpleNamespace(
        rag_release_id=SimpleNamespace(value=reusable_release.release_id)
    )
    report = {
        "rag_release_id": reusable_release.release_id,
        "built_stages": reusable_release.built_stages,
        "reused_stages": reusable_release.reused_stages,
    }
    return snapshot, release, report, reusable_release.build_attempt


# ---------------------------------------------------------------------------
# LIVE TEST
# ---------------------------------------------------------------------------

@pytest.mark.corpus
@pytest.mark.bge_runtime
@pytest.mark.postgres_live
def test_live_hybrid_retrieval_question_bank(capsys, request) -> None:
    started_total = time.monotonic()
    e2e = _load_e2e_module()
    selected_questions = _selected_question_bank()
    progress = e2e._Progress(capsys, total_steps=12)

    progress.step("validating local corpus, DSN and seeded RAG variant")

    if not e2e._RAW_ROOT.exists():
        pytest.skip(f"corpus ausente: {e2e._RAW_ROOT}")

    raw_relpaths = e2e._raw_relpaths()
    assert raw_relpaths, f"corpus raw vacio: {e2e._RAW_ROOT}"

    dsn = e2e._dsn()
    if not dsn:
        pytest.skip("sin DSN PostgreSQL")

    e2e._assert_local_e2e_dsn(dsn)

    if not e2e._variant_seeded(dsn):
        pytest.skip(
            "proyecto/variante no sembrados; "
            "corre scripts/rag_platform/seed_project.py"
        )

    e2e._acquire_e2e_lock()

    reusable_state_is_valid = False
    reusable_state = _reusable_live_state(
        e2e,
        dsn=dsn,
        raw_relpaths=raw_relpaths,
    )
    reuse_existing_state = reusable_state is not None

    def _cleanup_after_test() -> None:
        try:
            if _should_preserve_live_state_after_test(
                force_clean=False,
                reusable_state_is_valid=reusable_state_is_valid,
            ):
                progress.step("preserving local LIVE hybrid state for reuse")
                progress.detail("derived state preserved for the next rerun")
        finally:
            e2e._release_e2e_lock()

    request.addfinalizer(_cleanup_after_test)

    if reuse_existing_state:
        revisions = reusable_state.revisions
        revision_relpaths = reusable_state.revision_relpaths
        progress.step("reusing existing release plus normalized chunk and embedding artifacts")
        progress.detail(
            f"release={reusable_state.release_id} "
            f"project_root={e2e._PROJECT_ROOT} "
            f"questions={len(selected_questions)}/{len(SST_E2E_QUESTIONS)}"
        )
        progress.step("verifying cached source revisions cover the real raw corpus")
    else:
        progress.step("running real raw ingestion and normalization")
        ingestion_cli = e2e._load(
            "run_project_ingestion_hybrid_live",
            "scripts/rag_platform/run_project_ingestion.py",
        )
        rc = ingestion_cli.main(
            [
                "--project-id",
                _PROJECT_ID,
                "--rag-variant-id",
                _VARIANT_ID,
                "--normalize",
                "--force",
            ]
        )
        assert rc == 0, "raw+normalize reporto fallos"
        capsys.readouterr()

        progress.step("verifying source revisions cover the real raw corpus")
        revisions = tuple(e2e._source_revisions_for_project(dsn))
        revision_relpaths = tuple(relpath for relpath, _ in revisions)

    assert revisions
    assert len(revisions) == len(raw_relpaths)
    assert set(revision_relpaths) == set(raw_relpaths)
    progress.detail(
        f"raw_documents={len(raw_relpaths)} revisions={len(revisions)}"
    )

    progress.step("preflight: one minimal real BGE forward")
    # _embed_questions_with_native_retry (mas abajo) ya revisa este mismo cache
    # y devuelve sin tocar BGE si hay hit -- si eso va a pasar, el preflight es
    # riesgo puro sin beneficio (solo protege el build, que tambien se reusa).
    cached_query_vectors = e2e.load_cached_query_embeddings(
        project_root=e2e._PROJECT_ROOT,
        embedding_profile_id=_EMBEDDING_PROFILE_ID,
        questions=SST_E2E_QUESTIONS,
    )
    if cached_query_vectors is not None:
        progress.detail(
            f"cached query embeddings found for {len(SST_E2E_QUESTIONS)} questions; skipping BGE preflight"
        )
    else:
        e2e._run_bge_preflight(dsn, progress=progress)

    progress.step("building a real RAG release")
    with e2e._Heartbeat("live hybrid release build"):
        snapshot, release, build_report, build_attempt = (
            _build_release_with_optional_reuse(
                e2e,
                dsn=dsn,
                revisions=revisions,
                progress=progress,
                reusable_release=reusable_state,
            )
        )

    release_id = release.rag_release_id.value
    assert str(build_report["rag_release_id"]) == release_id
    progress.detail(
        f"release={release_id} "
        f"snapshot={snapshot.corpus_snapshot_id.value} "
        f"built={build_report['built_stages']} "
        f"reused={build_report['reused_stages']}"
    )

    progress.step("verifying release memberships and physical vectors")
    embedding_profile, persistence = e2e._release_integrity_facts(
        dsn,
        release_id=release_id,
        expected_revision_count=len(revisions),
    )
    assert int(persistence["vector_total"]) > 0
    reusable_state_is_valid = True

    progress.step("embedding the SST hybrid question bank with BGE-M3 worker")
    query_vectors = e2e._embed_questions_with_native_retry(
        dsn,
        progress=progress,
    )
    assert len(query_vectors) == len(SST_E2E_QUESTIONS)
    assert all(
        len(vector) == embedding_profile.dimension
        for vector in query_vectors
    )

    progress.step("running REAL hybrid RetrievalSearchService over PostgreSQL")

    connection = e2e._connect(dsn)
    connection.autocommit = True
    try:
        indexing_target_id, corpus_version = _release_lane(
            connection,
            release_id=release_id,
        )

        profiles = PostgresEmbeddingProfileRepository(connection)
        targets = PostgresIndexingTargetRepository(connection)
        retrieval_profiles = PostgresRetrievalProfileRepository(connection)

        target = targets.get(indexing_target_id)
        assert target.vector_table == _VECTOR_TABLE

        vectors_by_query = dict(zip(SST_E2E_QUESTIONS, query_vectors))
        query_embedding = _PrecomputedRealQueryEmbedding(
            embedding_profile=embedding_profile,
            vectors_by_query=vectors_by_query,
        )
        vector_search = _ReleaseScopedVectorSearch(
            connection,
            release_id=release_id,
        )
        lexical_search = _ReleaseScopedLexicalSearch(
            connection,
            release_id=release_id,
        )
        parent_expansion = _ReleaseScopedParentExpansion(
            connection,
            release_id=release_id,
        )

        retrieval_profile = RetrievalProfile.build(
            project_id=_PROJECT_ID,
            consumer_scope_type="chatbot",
            consumer_scope_id=_CONSUMER_SCOPE_ID,
            corpus_version=corpus_version,
            embedding_profile_id=_EMBEDDING_PROFILE_ID,
            indexing_target_id=indexing_target_id,
            lexical_fallback_policy="allowed_when_vector_unavailable",
        ).model_copy(
            update={
                "active": True,
                "validation_status": "passed",
                "validated_at": datetime.now(timezone.utc),
            }
        )

        persisted_profile = retrieval_profiles.upsert(retrieval_profile)

        service = RetrievalSearchService(
            retrieval_profiles=retrieval_profiles,
            profiles=profiles,
            targets=targets,
            query_embedding=query_embedding,
            vector_search=vector_search,
            lexical_search=lexical_search,
            parent_expansion=parent_expansion,
        )

        release_scope = _release_lexical_scope_facts(
            connection,
            release_id=release_id,
            corpus_version=corpus_version,
        )
        progress.detail(
            "release lexical scope: "
            f"memberships={release_scope['memberships']} "
            f"chunk_bundles={release_scope['chunk_bundles']} "
            f"child_release={release_scope['child_nodes_release']} "
            f"child_visible={release_scope['child_nodes_visible']}"
        )

        smoke_results: list[dict[str, object]] = []
        for smoke_query in _SMOKE_QUERIES:
            _ = lexical_search.search(
                project_id=_PROJECT_ID,
                query=smoke_query,
                embedding_profile_id=_EMBEDDING_PROFILE_ID,
                corpus_version=corpus_version,
                top_k=_TOP_K,
            )
            smoke_result = dict(lexical_search.last_result or {})
            smoke_result["query"] = smoke_query
            smoke_results.append(smoke_result)
            progress.detail(
                f"smoke lexical query={smoke_query!r} "
                f"candidates={int(smoke_result.get('candidate_count', 0) or 0)} "
                f"mode={smoke_result.get('query_mode') or '-'}"
            )

        lexical_search.calls.clear()
        lexical_search.last_result = None

        results: list[tuple[int, str, list[RetrievedEvidence]]] = []
        query_diagnostics: dict[int, dict[str, object]] = {}

        for position, (number, question) in enumerate(selected_questions, start=1):
            progress.question(position, len(selected_questions), question)
            started = time.monotonic()

            hits = service.search(
                retrieval_profile=persisted_profile,
                query=question,
                top_k=_TOP_K,
            )
            diagnostic = _collect_query_diagnostic(
                number=number,
                question=question,
                hits=hits,
                vector_result=vector_search.last_result,
                lexical_result=lexical_search.last_result,
            )
            query_diagnostics[number] = diagnostic

            progress.detail(
                f"q{number:02d} done hits={len(hits)} "
                f"vector_candidates={diagnostic['vector_candidates_count']} "
                f"lexical_candidates={diagnostic['lexical_candidates_count']} "
                f"overlap={diagnostic['vector_lexical_overlap_count']} "
                f"mode={diagnostic['lexical_query_mode'] or '-'} "
                f"in {time.monotonic() - started:.2f}s"
            )
            results.append((number, question, list(hits)))

        # IMPORTANT:
        # Persist the real retrieval evidence BEFORE any quality assertion.
        # A relevance/fusion/dedup regression must leave the Markdown report
        # available for diagnosis.
        progress.step("writing real hybrid retrieval report")
        _write_live_report(
            release_id=release_id,
            build_attempt=build_attempt,
            profile=embedding_profile,
            persistence=persistence,
            indexing_target_id=indexing_target_id,
            corpus_version=corpus_version,
            release_scope=release_scope,
            smoke_results=smoke_results,
            query_diagnostics=query_diagnostics,
            results=results,
            documents=revision_relpaths,
            elapsed_seconds=time.monotonic() - started_total,
        )
        progress.detail(f"report={_REPORT_PATH.name}")

        # Prove the diagnostic artifact exists before running quality asserts.
        assert _REPORT_PATH.is_file(), (
            f"no se genero el reporte esperado: {_REPORT_PATH}"
        )
        report = _REPORT_PATH.read_text(encoding="utf-8")
        assert "respuesta relevante para" not in report
        assert "coincidencia lexical exacta para" not in report

        for number, question in selected_questions:
            assert f"### q{number:02d}. {question}" in report

        # ------------------------------------------------------------------
        # Assertions AFTER report persistence
        # ------------------------------------------------------------------

        # Always-on hybrid: every real question must have called both signals.
        assert len(vector_search.calls) == len(selected_questions)
        assert len(lexical_search.calls) == len(selected_questions)
        assert query_embedding.queries == [
            question for _number, question in selected_questions
        ]
        assert [call["query"] for call in lexical_search.calls] == [
            question for _number, question in selected_questions
        ]

        # Validate every result only after the report already exists.
        for number, question, hits in results:
            _assert_real_result_rules(
                number=number,
                question=question,
                hits=hits,
                release_id=release_id,
            )

        results_by_number = {
            number: hits for number, _question, hits in results
        }

        # Concrete relevance regressions observed in the dense-only E2E.
        if 1 in results_by_number:
            _assert_q01_native_policy_source(results_by_number[1])
        if 15 in results_by_number:
            _assert_q15_arl_lexical_rescue(results_by_number[15])

        summary = _summarize_query_diagnostics(query_diagnostics)
        smoke_candidates_total = sum(
            int(result.get("candidate_count", 0) or 0)
            for result in smoke_results
        )
        smoke_failures = [
            result
            for result in smoke_results
            if result.get("exception")
        ]

        assert release_scope["child_nodes_visible"] > 0, (
            "el release no tiene child nodes lexicalmente visibles; "
            "revisar joins release->chunk_bundle->indexing_nodes"
        )
        assert not smoke_failures, (
            "las smoke queries lexicales fallaron: "
            f"{smoke_failures!r}"
        )
        assert smoke_candidates_total > 0, (
            "las smoke queries lexicales no devolvieron candidatos reales"
        )
        assert summary["raw_vector_candidates_total"] > 0
        assert summary["raw_lexical_candidates_total"] > 0, (
            "el benchmark hibrido sigue sin candidatos lexicales reales"
        )
        assert summary["queries_with_lexical_candidates"] > 0, (
            "ninguna pregunta produjo candidatos lexicales"
        )
        assert summary["lexical_hybrid_failures"] == 0, (
            "hubo fallas reales del lane lexical durante hybrid"
        )
        assert summary["final_vector_lexical_hits"] > 0, (
            "las consultas reales no produjeron ningun hit fusionado "
            "vector+lexical; revisar hybrid always-on"
        )

    finally:
        connection.close()
