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

        return [
            _row_to_evidence(
                row,
                source="vector",
                embedding_profile_id=embedding_profile_id,
                corpus_version=corpus_version,
                release_id=self._release_id,
            )
            for row in rows
        ]


class _ReleaseScopedLexicalSearch:
    """Real PostgreSQL Spanish FTS restricted to the release's chunk bundles."""

    def __init__(self, connection: object, *, release_id: str) -> None:
        self._connection = connection
        self._release_id = release_id
        self.calls: list[dict[str, object]] = []

    def search(
        self,
        *,
        project_id: str,
        query: str,
        embedding_profile_id: str,
        corpus_version: str,
        top_k: int,
    ) -> list[RetrievedEvidence]:
        self.calls.append({"query": query, "top_k": top_k})

        with self._connection.cursor() as cursor:
            tsvector = " || ".join([
                "setweight(to_tsvector('spanish', COALESCE(n.section_title, '')), 'A')",
                "setweight(to_tsvector('spanish', COALESCE(n.section_path, '')), 'B')",
                "setweight(to_tsvector('spanish', "
                "array_to_string(regexp_to_array("
                "COALESCE((SELECT string_agg(tok, ' ') FROM unnest(regexp_split_to_array("
                "regexp_replace("
                "regexp_replace(COALESCE(n.source_relpath, ''), E'.*[/\\\\\\\\]', '', 'g'),"
                " E'\\\\.[^.]*$', '', 'g'),"
                " E'[/\\\\\\\\]+', ' ')) AS tok"
                " WHERE lower(tok) NOT IN ('general_sst','manuales','organizacion',"
                "'capacitaciones','protocolos','normas_seguridad','riesgos',"
                "'canales_comunicacion','comunicaciones','riesgo_fisico',"
                "'aspectos_ambientales','preferidos','respaldo') AND tok <> ''), ' ')), ' ')), 'C')",
                "setweight(to_tsvector('spanish', "
                "array_to_string(regexp_to_array("
                "regexp_replace("
                "regexp_replace(COALESCE(n.source_relpath, ''), E'.*[/\\\\\\\\]', '', 'g'),"
                " E'\\\\.[^.]*$', '', 'g'),"
                " E'[^a-zA-Z\\\\u00C0-\\\\u024F]+', ' ', 'g'),"
                " ' '), ' ')), 'A')",
                "setweight(to_tsvector('spanish', n.text), 'C')",
            ])
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
                        plainto_tsquery('spanish', %s)
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
                  AND ({tsvector}) @@ plainto_tsquery('spanish', %s)
                ORDER BY score DESC
                LIMIT %s
                """,
                (
                    query,
                    project_id,
                    corpus_version,
                    self._release_id,
                    query,
                    top_k,
                ),
            )
            rows = list(cursor.fetchall())

        return [
            _row_to_evidence(
                row,
                source="lexical",
                embedding_profile_id=embedding_profile_id,
                corpus_version=corpus_version,
                release_id=self._release_id,
            )
            for row in rows
        ]


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


def _write_live_report(
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

            snippet = _md(hit.text)[:1200]

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


def _force_clean_live_state() -> bool:
    return os.environ.get("CHATBOT_SST_LIVE_RETRIEVAL_FORCE_CLEAN", "0") == "1"


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
    run_completed: bool,
) -> bool:
    return run_completed and not force_clean


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
    if _force_clean_live_state():
        return None
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
    progress = e2e._Progress(capsys, total_steps=11)

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

    owned_retrieval_profile_id: str | None = None
    run_completed = False
    reusable_state = _reusable_live_state(
        e2e,
        dsn=dsn,
        raw_relpaths=raw_relpaths,
    )
    reuse_existing_state = reusable_state is not None

    def _cleanup_after_test() -> None:
        try:
            if owned_retrieval_profile_id:
                connection = e2e._connect(dsn)
                try:
                    with connection:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "DELETE FROM retrieval_profiles "
                                "WHERE retrieval_profile_id = %s",
                                (owned_retrieval_profile_id,),
                            )
                finally:
                    connection.close()

            if _should_preserve_live_state_after_test(
                force_clean=_force_clean_live_state(),
                run_completed=run_completed,
            ):
                progress.step("preserving local LIVE hybrid state for reuse")
                progress.detail(
                    "set CHATBOT_SST_LIVE_RETRIEVAL_FORCE_CLEAN=1 to force "
                    "a fresh rebuild on the next run"
                )
            else:
                progress.step("hard deleting local LIVE hybrid state")
                deleted = e2e._hard_delete_e2e_project_state(
                    dsn,
                    raw_relpaths=raw_relpaths,
                )
                progress.detail(
                    f"post-test cleanup: {e2e._format_deleted_counts(deleted)}"
                )
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
            f"questions={len(SST_E2E_QUESTIONS)}"
        )
        progress.step("verifying cached source revisions cover the real raw corpus")
    else:
        progress.step("hard deleting stale local E2E/LIVE state")
        deleted = e2e._hard_delete_e2e_project_state(
            dsn,
            raw_relpaths=raw_relpaths,
        )
        progress.detail(f"pre-test cleanup: {e2e._format_deleted_counts(deleted)}")

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
        owned_retrieval_profile_id = persisted_profile.retrieval_profile_id

        service = RetrievalSearchService(
            retrieval_profiles=retrieval_profiles,
            profiles=profiles,
            targets=targets,
            query_embedding=query_embedding,
            vector_search=vector_search,
            lexical_search=lexical_search,
            parent_expansion=parent_expansion,
        )

        results: list[tuple[str, list[RetrievedEvidence]]] = []

        for index, question in enumerate(SST_E2E_QUESTIONS, start=1):
            progress.question(index, len(SST_E2E_QUESTIONS), question)
            started = time.monotonic()

            hits = service.search(
                retrieval_profile=persisted_profile,
                query=question,
                top_k=_TOP_K,
            )

            progress.detail(
                f"q{index} done hits={len(hits)} "
                f"in {time.monotonic() - started:.2f}s"
            )
            results.append((question, list(hits)))

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

        for number, question in enumerate(SST_E2E_QUESTIONS, start=1):
            assert f"### q{number:02d}. {question}" in report

        # ------------------------------------------------------------------
        # Assertions AFTER report persistence
        # ------------------------------------------------------------------

        # Always-on hybrid: every real question must have called both signals.
        assert len(vector_search.calls) == len(SST_E2E_QUESTIONS)
        assert len(lexical_search.calls) == len(SST_E2E_QUESTIONS)
        assert query_embedding.queries == list(SST_E2E_QUESTIONS)
        assert [call["query"] for call in lexical_search.calls] == list(
            SST_E2E_QUESTIONS
        )

        # Validate every result only after the report already exists.
        for number, (question, hits) in enumerate(results, start=1):
            _assert_real_result_rules(
                number=number,
                question=question,
                hits=hits,
                release_id=release_id,
            )

        # Concrete relevance regressions observed in the dense-only E2E.
        _assert_q01_native_policy_source(results[0][1])
        _assert_q15_arl_lexical_rescue(results[14][1])

        # At least one final candidate must have been present in both signals.
        fused_hits = [
            hit
            for _question, hits in results
            for hit in hits
            if {"vector", "lexical"}
            <= set(
                str(value)
                for value in (hit.metadata or {}).get(
                    "fusion_sources",
                    [],
                )
            )
        ]
        assert fused_hits, (
            "las consultas reales no produjeron ningun hit fusionado "
            "vector+lexical; revisar hybrid always-on"
        )
        run_completed = True

    finally:
        connection.close()
