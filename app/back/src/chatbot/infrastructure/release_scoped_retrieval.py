"""Release-scoped retrieval adapters for chatbot dispatch."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
import math
import re

from chatbot.application.ports import (
    ChatbotReleaseLane,
    ChatbotReleaseRetrievalPort,
    ChatbotReleaseRetrievalResult,
)
from chatbot.domain.errors import ChatbotReleaseLaneUnavailable
from embedding.application.ports import (
    EmbeddingBundleRepository,
    EmbeddingProfileRepository,
)
from indexing.application.bundle_first.ports import IndexingTargetRepository
from indexing.infrastructure.in_memory.bundle_first import (
    InMemoryBundleVectorRepository,
    InMemoryIndexingNodeWriter,
    InMemoryIndexingRunRepository,
)
from retrieval.application.query_embedding_service import QueryEmbeddingService
from retrieval.application.retrieval_service import RetrievalSearchService
from retrieval.domain.models import RetrievalProfile, RetrievedEvidence
from retrieval.infrastructure.faq_resolver import FaqResolverRegistry
from retrieval.infrastructure.in_memory.repositories import InMemoryRetrievalProfileRepository
from retrieval.infrastructure.postgres.repositories import (
    _fts_query_modes,
    _tsquery_sql,
    _tsvector_sql,
)
from retrieval.reranking import NoOpReranker


def _now() -> datetime:
    return datetime.now(UTC)


def _evidence_from_node(
    *,
    node,
    score: float,
    source: str,
    embedding_profile_id: str,
    corpus_version: str,
    embedding_bundle_id: str | None,
    rag_release_id: str,
    project_id: str,
) -> RetrievedEvidence:
    return RetrievedEvidence(
        node_id=node.node_id,
        document_id=node.document_id,
        parent_node_id=node.parent_node_id,
        child_chunk_id=node.node_id,
        text=node.text,
        score=score,
        source=source,  # type: ignore[arg-type]
        page_start=node.page_start,
        page_end=node.page_end,
        section_title=node.section_title,
        section_path=node.section_path,
        metadata={
            **dict(node.metadata),
            "rag_release_id": rag_release_id,
            "source_relpath": node.source_relpath,
            # G1: project_id acompaña la evidencia para que el chatbot pueda
            # construir la cita project-aware (_build_source_url); ya viaja como
            # parámetro de .search()/.expand(), aquí solo se propaga al metadata.
            "project_id": project_id,
        },
        embedding_profile_id=embedding_profile_id,
        corpus_version=corpus_version,
        embedding_bundle_id=embedding_bundle_id,
    )


@dataclass(frozen=True)
class _ReleaseScope:
    lane: ChatbotReleaseLane
    embedding_bundle_ids: frozenset[str]
    chunk_bundle_ids: frozenset[str]


class InMemoryReleaseScopedRetrievalPort(ChatbotReleaseRetrievalPort):
    """Search one release from in-memory pipeline state."""

    def __init__(
        self,
        *,
        indexing_runs: InMemoryIndexingRunRepository,
        bundles: EmbeddingBundleRepository,
        profiles: EmbeddingProfileRepository,
        targets: IndexingTargetRepository,
        retrieval_profiles: InMemoryRetrievalProfileRepository,
        query_embedding: QueryEmbeddingService,
        vectors: InMemoryBundleVectorRepository,
        nodes: InMemoryIndexingNodeWriter,
        reranker: object | None = None,
    ) -> None:
        self._indexing_runs = indexing_runs
        self._bundles = bundles
        self._profiles = profiles
        self._targets = targets
        self._retrieval_profiles = retrieval_profiles
        self._query_embedding = query_embedding
        self._vectors = vectors
        self._nodes = nodes
        self._reranker = reranker or NoOpReranker()

    def search(
        self,
        *,
        project_id: str,
        rag_variant_id: str,
        rag_release_id: str,
        question: str,
        top_k: int,
    ) -> ChatbotReleaseRetrievalResult:
        scope = self._resolve_scope(
            project_id=project_id,
            rag_variant_id=rag_variant_id,
            rag_release_id=rag_release_id,
        )
        retrieval_profile = _release_profile(
            project_id=project_id,
            lane=scope.lane,
        )
        self._retrieval_profiles.upsert(retrieval_profile)
        service = RetrievalSearchService(
            retrieval_profiles=self._retrieval_profiles,
            profiles=self._profiles,
            targets=self._targets,
            query_embedding=self._query_embedding,
            vector_search=_InMemoryReleaseScopedVectorSearch(
                vectors=self._vectors,
                nodes=self._nodes,
                embedding_bundle_ids=scope.embedding_bundle_ids,
                rag_release_id=rag_release_id,
            ),
            lexical_search=_InMemoryReleaseScopedLexicalSearch(
                nodes=self._nodes,
                chunk_bundle_ids=scope.chunk_bundle_ids,
                rag_release_id=rag_release_id,
            ),
            parent_expansion=_InMemoryReleaseScopedParentExpansion(
                nodes=self._nodes,
                chunk_bundle_ids=scope.chunk_bundle_ids,
                rag_release_id=rag_release_id,
            ),
            reranker=self._reranker,
        )
        evidence = service.search(
            retrieval_profile=retrieval_profile,
            query=question,
            top_k=top_k,
        )
        return ChatbotReleaseRetrievalResult(
            lane=scope.lane,
            evidence=tuple(evidence),
            retrieval_profile_id=retrieval_profile.retrieval_profile_id,
        )

    def _resolve_scope(
        self,
        *,
        project_id: str,
        rag_variant_id: str,
        rag_release_id: str,
    ) -> _ReleaseScope:
        matching_runs = [
            run
            for run in self._indexing_runs.list_runs()
            if run.project_id == project_id
            and run.rag_variant_id == rag_variant_id
            and run.rag_release_id == rag_release_id
            and run.status == "completed"
            and run.embedding_bundle_id
            and run.embedding_profile_id
            and run.indexing_target_id
            and run.corpus_version
        ]
        if not matching_runs:
            raise ChatbotReleaseLaneUnavailable(
                "no completed indexing run is available for the requested "
                "project_id/rag_variant_id/rag_release_id"
            )
        lane_keys = {
            (
                str(run.embedding_profile_id),
                str(run.indexing_target_id),
                str(run.corpus_version),
            )
            for run in matching_runs
        }
        if len(lane_keys) != 1:
            raise ChatbotReleaseLaneUnavailable(
                "the requested release resolves more than one retrieval lane; "
                "dispatch is blocked fail-closed"
            )
        embedding_bundle_ids = {
            str(run.embedding_bundle_id) for run in matching_runs if run.embedding_bundle_id
        }
        chunk_bundle_ids = {
            self._bundles.get(bundle_id).source_chunk_bundle_id
            for bundle_id in embedding_bundle_ids
        }
        embedding_profile_id, indexing_target_id, corpus_version = next(iter(lane_keys))
        return _ReleaseScope(
            lane=ChatbotReleaseLane(
                embedding_profile_id=embedding_profile_id,
                indexing_target_id=indexing_target_id,
                corpus_version=corpus_version,
            ),
            embedding_bundle_ids=frozenset(embedding_bundle_ids),
            chunk_bundle_ids=frozenset(str(bundle_id) for bundle_id in chunk_bundle_ids),
        )


class _InMemoryReleaseScopedVectorSearch:
    def __init__(
        self,
        *,
        vectors: InMemoryBundleVectorRepository,
        nodes: InMemoryIndexingNodeWriter,
        embedding_bundle_ids: frozenset[str],
        rag_release_id: str,
    ) -> None:
        self._vectors = vectors
        self._nodes = nodes
        self._embedding_bundle_ids = embedding_bundle_ids
        self._rag_release_id = rag_release_id

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
        del distance_metric
        scored: list[RetrievedEvidence] = []
        for (table, bundle_id, node_id), stored in self._vectors.rows.items():
            if table != vector_table or bundle_id not in self._embedding_bundle_ids:
                continue
            if (
                stored.record.project_id != project_id
                or stored.embedding_profile_id != embedding_profile_id
                or stored.indexing_target_id != indexing_target_id
                or stored.record.corpus_version != corpus_version
            ):
                continue
            node = self._nodes.nodes.get(node_id)
            if node is None:
                continue
            scored.append(
                _evidence_from_node(
                    node=node,
                    score=_cosine(query_embedding, stored.record.embedding),
                    source="vector",
                    embedding_profile_id=embedding_profile_id,
                    corpus_version=corpus_version,
                    embedding_bundle_id=stored.record.embedding_bundle_id,
                    rag_release_id=self._rag_release_id,
                    project_id=project_id,
                )
            )
        return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]


class _InMemoryReleaseScopedLexicalSearch:
    def __init__(
        self,
        *,
        nodes: InMemoryIndexingNodeWriter,
        chunk_bundle_ids: frozenset[str],
        rag_release_id: str,
    ) -> None:
        self._nodes = nodes
        self._chunk_bundle_ids = chunk_bundle_ids
        self._rag_release_id = rag_release_id

    def search(
        self,
        *,
        project_id: str,
        query: str,
        embedding_profile_id: str,
        corpus_version: str,
        top_k: int,
    ) -> list[RetrievedEvidence]:
        terms = {token for token in query.lower().split() if token}
        scored: list[RetrievedEvidence] = []
        for node in self._nodes.nodes.values():
            if (
                node.node_role != "child"
                or node.project_id != project_id
                or node.corpus_version != corpus_version
                or node.source_chunk_bundle_id not in self._chunk_bundle_ids
            ):
                continue
            tokens = {token for token in node.text.lower().split() if token}
            overlap = len(terms & tokens)
            if overlap == 0:
                continue
            scored.append(
                _evidence_from_node(
                    node=node,
                    score=float(overlap),
                    source="lexical",
                    embedding_profile_id=embedding_profile_id,
                    corpus_version=corpus_version,
                    embedding_bundle_id=None,
                    rag_release_id=self._rag_release_id,
                    project_id=project_id,
                )
            )
        return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]


class _InMemoryReleaseScopedParentExpansion:
    def __init__(
        self,
        *,
        nodes: InMemoryIndexingNodeWriter,
        chunk_bundle_ids: frozenset[str],
        rag_release_id: str,
    ) -> None:
        self._nodes = nodes
        self._chunk_bundle_ids = chunk_bundle_ids
        self._rag_release_id = rag_release_id

    def expand(
        self,
        *,
        project_id: str,
        parent_node_ids: Sequence[str],
        embedding_profile_id: str,
        corpus_version: str,
    ) -> dict[str, RetrievedEvidence]:
        parents: dict[str, RetrievedEvidence] = {}
        for parent_node_id in parent_node_ids:
            node = self._nodes.nodes.get(parent_node_id)
            if (
                node is None
                or node.project_id != project_id
                or node.corpus_version != corpus_version
                or node.source_chunk_bundle_id not in self._chunk_bundle_ids
            ):
                continue
            parents[parent_node_id] = _evidence_from_node(
                node=node,
                score=0.0,
                source="lexical",
                embedding_profile_id=embedding_profile_id,
                corpus_version=corpus_version,
                embedding_bundle_id=None,
                rag_release_id=self._rag_release_id,
                project_id=project_id,
            )
        return parents


class PostgresReleaseScopedRetrievalPort(ChatbotReleaseRetrievalPort):
    """Search one published release from durable PostgreSQL state."""

    def __init__(
        self,
        *,
        connection: object,
        profiles: EmbeddingProfileRepository,
        targets: IndexingTargetRepository,
        retrieval_profiles,
        query_embedding: QueryEmbeddingService,
        reranker: object | None = None,
        faq_resolver_registry: FaqResolverRegistry | None = None,
    ) -> None:
        self._connection = connection
        self._profiles = profiles
        self._targets = targets
        self._retrieval_profiles = retrieval_profiles
        self._query_embedding = query_embedding
        self._reranker = reranker or NoOpReranker()
        # Optional fast lexical/fuzzy FAQ shortcut, one resolver per project (PR-3 3.1/3.2 — no
        # more single global resolver / glob()[0] cross-project leak). Checked first (sub-10ms);
        # on a confident hit whose citation is verified to belong to the release (PR-3 3.3,
        # ``_faq_result``) the embedding + vector + rerank path never runs. On a miss, or a hit
        # that fails the release-membership gate, the full retrieval proceeds.
        self._faq_resolver_registry = faq_resolver_registry

    def search(
        self,
        *,
        project_id: str,
        rag_variant_id: str,
        rag_release_id: str,
        question: str,
        top_k: int,
    ) -> ChatbotReleaseRetrievalResult:
        del rag_variant_id
        # Resolved once up front: both the FAQ release-membership gate (PR-3 3.3) and the real
        # search below need it, and a release with no valid lane must fail the same way whether
        # or not a FAQ entry would otherwise have matched (no synthetic "faq" lane bypasses this).
        lane = self._resolve_lane(project_id=project_id, rag_release_id=rag_release_id)
        # FAQ-first: milliseconds vs seconds for the embed, so checking here means the embedding
        # path never starts on a hit ("si esta en FAQ se para el embedding, si no continua"). One
        # resolver per project (PR-3 3.1/3.2); a hit only answers if it clears the release-
        # membership gate in ``_faq_result`` (PR-3 3.3) — otherwise it falls through below.
        if self._faq_resolver_registry is not None:
            resolver = self._faq_resolver_registry.resolver_for(project_id)
            if resolver is not None:
                match = resolver.match(question)
                if match is not None:
                    faq_result = self._faq_result(
                        match, project_id=project_id, rag_release_id=rag_release_id
                    )
                    if faq_result is not None:
                        return faq_result
        retrieval_profile = _release_profile(project_id=project_id, lane=lane)
        self._retrieval_profiles.upsert(retrieval_profile)
        service = RetrievalSearchService(
            retrieval_profiles=self._retrieval_profiles,
            profiles=self._profiles,
            targets=self._targets,
            query_embedding=self._query_embedding,
            vector_search=_PostgresReleaseScopedVectorSearch(
                connection=self._connection,
                rag_release_id=rag_release_id,
            ),
            lexical_search=_PostgresReleaseScopedLexicalSearch(
                connection=self._connection,
                rag_release_id=rag_release_id,
            ),
            parent_expansion=_PostgresReleaseScopedParentExpansion(
                connection=self._connection,
                rag_release_id=rag_release_id,
            ),
            reranker=self._reranker,
        )
        evidence = service.search(
            retrieval_profile=retrieval_profile,
            query=question,
            top_k=top_k,
        )
        return ChatbotReleaseRetrievalResult(
            lane=lane,
            evidence=tuple(evidence),
            retrieval_profile_id=retrieval_profile.retrieval_profile_id,
        )

    def _faq_result(
        self, match: object, *, project_id: str, rag_release_id: str
    ) -> ChatbotReleaseRetrievalResult | None:
        """Build a single-evidence result from a FAQ hit, gated to the release's evidence.

        PR-3 3.3: a curated FAQ entry can go stale — it may cite a document that was later
        removed, rejected in review, or never belonged to the queried release's corpus at all.
        Before this gate, any FAQ hit answered unconditionally via a synthetic ``faq`` lane that
        never touched Postgres, so a published release with an invalid/unbuilt lane could still
        answer from a FAQ entry with no real evidence behind it. Now the referenced document must
        be indexed, approved, and a member of ``rag_release_id`` (``_faq_reference_in_release``) —
        otherwise this returns ``None`` and the caller falls through to real, release-scoped
        retrieval instead of a stale or cross-release answer.
        """

        reference = getattr(match, "reference", None) or {}
        # References carry two key shapes (normalized_path / chunk_file); the FAQ's chunk_ids do
        # not match the live corpus (they are audit metadata, not link targets), so the citation
        # can only be verified via the file path.
        source_path = reference.get("normalized_path") or reference.get("chunk_file")
        if not source_path or not self._faq_reference_in_release(
            project_id=project_id,
            rag_release_id=rag_release_id,
            source_relpath=source_path,
        ):
            return None
        pages = reference.get("pages") or []
        page = int(pages[0]) if pages else None
        # Surface a clean, human document identity from document_title or the file's basename,
        # never the FAQ id or the stale chunk ids.
        document_title = reference.get("document_title")
        basename = (
            source_path.rsplit("/", 1)[-1]
            .replace(".child_chunks.jsonl", "")
            .replace(".program", "")
        )
        document_id = str(document_title or basename or match.faq_id)
        evidence = RetrievedEvidence(
            node_id=f"faq-{match.faq_id}",
            document_id=document_id,
            parent_node_id=None,
            child_chunk_id=f"faq-{match.faq_id}",
            text=match.answer,
            score=float(match.score),
            source="lexical",
            page_start=page,
            page_end=page,
            section_title=reference.get("document_title"),
            section_path=None,
            metadata={
                "faq_id": match.faq_id,
                "faq_status": match.status,
                "faq_score": f"{match.score:.3f}",
                "source_relpath": source_path,
                "rag_release_id": rag_release_id,
                "project_id": project_id,
            },
            embedding_profile_id="faq",
            corpus_version="faq",
            embedding_bundle_id=None,
        )
        lane = ChatbotReleaseLane(
            embedding_profile_id="faq",
            indexing_target_id="faq",
            corpus_version="faq",
        )
        # Same identity function as the real lane so the reported id is always the
        # one that "searched" -- here, the synthetic faq lane, never a rebuilt profile.
        retrieval_profile_id = _release_profile(project_id=project_id, lane=lane).retrieval_profile_id
        return ChatbotReleaseRetrievalResult(
            lane=lane, evidence=(evidence,), retrieval_profile_id=retrieval_profile_id
        )

    def _faq_reference_in_release(
        self, *, project_id: str, rag_release_id: str, source_relpath: str
    ) -> bool:
        """True iff ``source_relpath`` is indexed, approved evidence of ``rag_release_id``.

        Mirrors the join ``_PostgresReleaseScopedLexicalSearch`` uses for real evidence, scoped to
        one exact path instead of full-text search — a FAQ's cited document must clear the same
        release-membership bar as any other piece of release evidence (PR-3 3.3).
        """

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM indexing_nodes AS node
                JOIN indexing_normalized_documents AS document
                  ON document.document_id = node.document_id
                WHERE node.project_id = %s
                  AND node.source_relpath = %s
                  AND document.processing_status = 'processed'
                  AND document.review_status = 'approved'
                  AND EXISTS (
                      SELECT 1
                      FROM rag_release_memberships AS membership
                      WHERE membership.rag_release_id = %s
                        AND membership.project_id = node.project_id
                        AND membership.chunk_bundle_id = node.source_chunk_bundle_id
                  )
                LIMIT 1
                """,
                (project_id, source_relpath, rag_release_id),
            )
            rows = list(cursor.fetchall())
        return bool(rows)

    def _resolve_lane(
        self,
        *,
        project_id: str,
        rag_release_id: str,
    ) -> ChatbotReleaseLane:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT
                    eb.embedding_profile_id,
                    im.indexing_target_id,
                    eb.corpus_version
                FROM rag_release_memberships AS m
                JOIN embedding_bundles AS eb
                  ON eb.embedding_bundle_id = m.embedding_bundle_id
                 AND eb.project_id = m.project_id
                JOIN indexing_materializations AS im
                  ON im.materialization_id = m.materialization_id
                 AND im.project_id = m.project_id
                WHERE m.project_id = %s
                  AND m.rag_release_id = %s
                """,
                (project_id, rag_release_id),
            )
            rows = list(cursor.fetchall())
        lane_keys = {
            (
                str(_value(row, "embedding_profile_id", 0)),
                str(_value(row, "indexing_target_id", 1)),
                str(_value(row, "corpus_version", 2)),
            )
            for row in rows
        }
        if not lane_keys:
            raise ChatbotReleaseLaneUnavailable(
                "no release-scoped retrieval lane is available for the requested "
                "project_id/rag_release_id"
            )
        if len(lane_keys) != 1:
            raise ChatbotReleaseLaneUnavailable(
                "the requested release resolves more than one retrieval lane; "
                "dispatch is blocked fail-closed"
            )
        embedding_profile_id, indexing_target_id, corpus_version = next(iter(lane_keys))
        return ChatbotReleaseLane(
            embedding_profile_id=embedding_profile_id,
            indexing_target_id=indexing_target_id,
            corpus_version=corpus_version,
        )


_VECTOR_TABLE_PATTERN = re.compile(r"^idx_vec_[a-z0-9_]+$")
_DISTANCE_OPERATOR = {
    "cosine": "<=>",
    "l2": "<->",
    "inner_product": "<#>",
}


class _PostgresReleaseScopedVectorSearch:
    def __init__(self, *, connection: object, rag_release_id: str) -> None:
        self._connection = connection
        self._rag_release_id = rag_release_id

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
            raise ValueError("vector table name is not a registered indexing target table")
        operator = _DISTANCE_OPERATOR[distance_metric]
        with self._connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    vector_row.node_id,
                    vector_row.document_id,
                    vector_row.embedding_bundle_id,
                    node.parent_node_id,
                    node.text,
                    node.page_start,
                    node.page_end,
                    node.section_title,
                    node.section_path,
                    node.metadata,
                    node.source_relpath,
                    1 - (vector_row.embedding {operator} %s::vector) AS score
                FROM {vector_table} AS vector_row
                JOIN indexing_nodes AS node
                  ON node.project_id = vector_row.project_id
                 AND node.node_id = vector_row.node_id
                JOIN indexing_normalized_documents AS document
                  ON document.document_id = vector_row.document_id
                WHERE vector_row.project_id = %s
                  AND node.project_id = %s
                  AND vector_row.embedding_profile_id = %s
                  AND vector_row.indexing_target_id = %s
                  AND vector_row.corpus_version = %s
                  AND document.processing_status = 'processed'
                  AND document.review_status = 'approved'
                  AND EXISTS (
                      SELECT 1
                      FROM rag_release_memberships AS membership
                      WHERE membership.rag_release_id = %s
                        AND membership.project_id = vector_row.project_id
                        AND membership.embedding_bundle_id = vector_row.embedding_bundle_id
                  )
                ORDER BY vector_row.embedding {operator} %s::vector
                LIMIT %s
                """,
                (
                    list(query_embedding),
                    project_id,
                    project_id,
                    embedding_profile_id,
                    indexing_target_id,
                    corpus_version,
                    self._rag_release_id,
                    list(query_embedding),
                    top_k,
                ),
            )
            rows = list(cursor.fetchall())
        return [
            _evidence_from_row(
                row=row,
                source="vector",
                embedding_profile_id=embedding_profile_id,
                corpus_version=corpus_version,
                rag_release_id=self._rag_release_id,
                project_id=project_id,
            )
            for row in rows
        ]


class _PostgresReleaseScopedLexicalSearch:
    def __init__(self, *, connection: object, rag_release_id: str) -> None:
        self._connection = connection
        self._rag_release_id = rag_release_id

    def search(
        self,
        *,
        project_id: str,
        query: str,
        embedding_profile_id: str,
        corpus_version: str,
        top_k: int,
    ) -> list[RetrievedEvidence]:
        with self._connection.cursor() as cursor:
            for mode in _fts_query_modes(query):
                tsvector = _tsvector_sql("node", config=mode.config)
                tsquery = _tsquery_sql(mode)
                cursor.execute(
                    f"""
                    SELECT
                        node.node_id,
                        node.document_id,
                        NULL AS embedding_bundle_id,
                        node.parent_node_id,
                        node.text,
                        node.page_start,
                        node.page_end,
                        node.section_title,
                        node.section_path,
                        node.metadata,
                        node.source_relpath,
                        ts_rank_cd(
                            {tsvector},
                            {tsquery}
                        ) AS score
                    FROM indexing_nodes AS node
                    JOIN indexing_normalized_documents AS document
                      ON document.document_id = node.document_id
                    WHERE node.node_role = 'child'
                      AND node.project_id = %s
                      AND node.corpus_version = %s
                      AND document.processing_status = 'processed'
                      AND document.review_status = 'approved'
                      AND EXISTS (
                          SELECT 1
                          FROM rag_release_memberships AS membership
                          WHERE membership.rag_release_id = %s
                            AND membership.project_id = node.project_id
                            AND membership.chunk_bundle_id = node.source_chunk_bundle_id
                      )
                      AND ({tsvector}) @@ {tsquery}
                    ORDER BY score DESC
                    LIMIT %s
                    """,
                    (
                        mode.query_text,
                        project_id,
                        corpus_version,
                        self._rag_release_id,
                        mode.query_text,
                        top_k,
                    ),
                )
                rows = list(cursor.fetchall())
                if not rows:
                    continue
                evidence = [
                    _evidence_from_row(
                        row=row,
                        source="lexical",
                        embedding_profile_id=embedding_profile_id,
                        corpus_version=corpus_version,
                        rag_release_id=self._rag_release_id,
                        project_id=project_id,
                    )
                    for row in rows
                ]
                return [
                    item.model_copy(
                        update={
                            "metadata": {
                                **item.metadata,
                                "fts_query_mode": mode.mode_name,
                            }
                        }
                    )
                    for item in evidence
                ]
        return []


class _PostgresReleaseScopedParentExpansion:
    def __init__(self, *, connection: object, rag_release_id: str) -> None:
        self._connection = connection
        self._rag_release_id = rag_release_id

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
                    node.node_id,
                    node.document_id,
                    NULL AS embedding_bundle_id,
                    node.parent_node_id,
                    node.text,
                    node.page_start,
                    node.page_end,
                    node.section_title,
                    node.section_path,
                    node.metadata,
                    node.source_relpath,
                    0.0 AS score
                FROM indexing_nodes AS node
                WHERE node.node_id = ANY(%s)
                  AND node.project_id = %s
                  AND node.node_role = 'parent'
                  AND node.corpus_version = %s
                  AND EXISTS (
                      SELECT 1
                      FROM rag_release_memberships AS membership
                      WHERE membership.rag_release_id = %s
                        AND membership.project_id = node.project_id
                        AND membership.chunk_bundle_id = node.source_chunk_bundle_id
                  )
                """,
                (
                    list(dict.fromkeys(parent_node_ids)),
                    project_id,
                    corpus_version,
                    self._rag_release_id,
                ),
            )
            rows = list(cursor.fetchall())
        evidence = [
            _evidence_from_row(
                row=row,
                source="lexical",
                embedding_profile_id=embedding_profile_id,
                corpus_version=corpus_version,
                rag_release_id=self._rag_release_id,
                project_id=project_id,
            )
            for row in rows
        ]
        return {item.node_id: item for item in evidence}


_EVIDENCE_COLUMNS = (
    "node_id",
    "document_id",
    "embedding_bundle_id",
    "parent_node_id",
    "text",
    "page_start",
    "page_end",
    "section_title",
    "section_path",
    "metadata",
    "source_relpath",
    "score",
)


def _evidence_from_row(
    *,
    row: Mapping[str, object] | Sequence[object],
    source: str,
    embedding_profile_id: str,
    corpus_version: str,
    rag_release_id: str,
    project_id: str,
) -> RetrievedEvidence:
    values = (
        dict(row)
        if isinstance(row, Mapping)
        else dict(zip(_EVIDENCE_COLUMNS, row))
    )
    metadata = (
        dict(values["metadata"])
        if isinstance(values["metadata"], Mapping)
        else {}
    )
    metadata["rag_release_id"] = rag_release_id
    metadata["source_relpath"] = str(values.get("source_relpath") or "")
    # G1: project_id acompaña la evidencia para la cita project-aware
    # (_build_source_url); ya viaja como parámetro de .search()/.expand().
    metadata["project_id"] = project_id
    return RetrievedEvidence(
        node_id=str(values["node_id"]),
        document_id=str(values["document_id"]),
        parent_node_id=(
            None if values["parent_node_id"] is None else str(values["parent_node_id"])
        ),
        child_chunk_id=str(values["node_id"]),
        text=str(values["text"] or ""),
        score=float(values["score"]),
        source=source,  # type: ignore[arg-type]
        page_start=values["page_start"],  # type: ignore[arg-type]
        page_end=values["page_end"],  # type: ignore[arg-type]
        section_title=values["section_title"],  # type: ignore[arg-type]
        section_path=values["section_path"],  # type: ignore[arg-type]
        metadata=metadata,
        embedding_profile_id=embedding_profile_id,
        corpus_version=corpus_version,
        embedding_bundle_id=(
            None
            if values["embedding_bundle_id"] is None
            else str(values["embedding_bundle_id"])
        ),
    )


def _release_profile(
    *,
    project_id: str,
    lane: ChatbotReleaseLane,
) -> RetrievalProfile:
    return RetrievalProfile.build(
        project_id=project_id,
        consumer_scope_type="chatbot",
        consumer_scope_id="release-scoped-dispatch",
        corpus_version=lane.corpus_version,
        embedding_profile_id=lane.embedding_profile_id,
        indexing_target_id=lane.indexing_target_id,
    ).model_copy(
        update={
            "active": True,
            "validation_status": "passed",
            "validated_at": _now(),
        }
    )


def _value(row: Mapping[str, object] | Sequence[object], key: str, index: int) -> object:
    if isinstance(row, Mapping):
        return row[key]
    return row[index]


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return numerator / (left_norm * right_norm)
