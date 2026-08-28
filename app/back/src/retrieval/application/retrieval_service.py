"""Retrieval profile use cases, readiness and the durable search flow.

Vector retrieval always runs against the physical table named by
``indexing_targets``; a browser can never supply a table name. Lexical retrieval
only answers alone when ``lexical_fallback_policy`` explicitly allows it.
"""

from __future__ import annotations

import logging
import time  # PROFTMP
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from core.logging.observability import EventStatus, ObservabilityDomain
from embedding.application.events import emit_pipeline_event
from embedding.application.ports import (
    EmbeddingProfileRepository,
    ReadinessCheckRepository,
)
from embedding.domain.errors import EmbeddingDomainError
from embedding.domain.models import ReadinessCheck
from indexing.application.bundle_first.ports import IndexingTargetRepository

from retrieval.application.ports import (
    LexicalSearchPort,
    ParentExpansionPort,
    RerankerPort,
    RetrievalProfileRepository,
    VectorSearchPort,
)
from retrieval.application.query_embedding_service import QueryEmbeddingService
from retrieval.domain.dedup import (
    content_fingerprint,
    format_source_rank,
    select_unique_slots,
)
from retrieval.domain.errors import (
    LexicalFallbackNotAllowed,
    RetrievalProfileBlocked,
)
from retrieval.domain.models import (
    RETRIEVAL_VALIDATOR_VERSION,
    RetrievalProfile,
    RetrievalReadiness,
    RetrievalRuntimeStatus,
    RetrievalValidation,
    RetrievedEvidence,
)
from retrieval.fusion import (
    RetrievedCandidate,
    reciprocal_rank_fusion,
    vector_primary_hybrid_fusion,
)
from retrieval.reranking import NoOpReranker

logger = logging.getLogger(__name__)

#: Query used by the controlled smoke validation. It is synthetic on purpose so
#: no real user question ever reaches ``readiness_checks``.
SMOKE_VALIDATION_QUERY = "validacion sintetica de recuperacion"

#: Piso por lane antes de fusionar/dedup: el corte final a ``top_k`` ocurre
#: DESPUÉS de descartar gemelos y excedentes por párrafo.
_MIN_HYBRID_CANDIDATE_POOL = 50

#: Máximo de hijos del mismo párrafo que sobreviven al dedup. El cupo por sí
#: solo no basta -- ``select_unique_slots`` además exige que el segundo hijo
#: no sea casi el mismo texto que el primero (ver ``texts``/complementary
#: gate en retrieval/domain/dedup.py); así un párrafo largo puede aportar 2
#: fragmentos SOLO si son realmente distintos, no una ventana solapada.
_MAX_CHILDREN_PER_PARENT = 2

#: Candidatos deduplicados que llegan al reranker antes del corte a top_k.
#: Con NoOpReranker esto no importa (solo trunca); con un reranker real le da
#: margen para corregir casi-empates de RRF que la fusión no puede distinguir.
_RERANK_POOL_SIZE = 30


def _now() -> datetime:
    return datetime.now(UTC)


def _hybrid_candidate_pool_size(top_k: int) -> int:
    """Overfetch per lane so fusion/dedup keeps enough survivors for answer quality."""

    return max(_MIN_HYBRID_CANDIDATE_POOL, top_k * 12)


@dataclass(frozen=True)
class CreateRetrievalProfileRequest:
    """Public payload for registering one retrieval profile."""

    project_id: str
    consumer_scope_type: str
    consumer_scope_id: str
    corpus_version: str
    embedding_profile_id: str
    indexing_target_id: str
    lexical_fallback_policy: str = "allowed_when_vector_unavailable"


@dataclass(frozen=True)
class SearchRetrievalRequest:
    """Public payload for one retrieval query against one active lane."""

    retrieval_profile_id: str
    query: str
    top_k: int = 10


class CreateRetrievalProfileUseCase:
    """Register one inactive retrieval profile."""

    def __init__(
        self,
        *,
        retrieval_profiles: RetrievalProfileRepository,
        profiles: EmbeddingProfileRepository,
        targets: IndexingTargetRepository,
    ) -> None:
        self._retrieval_profiles = retrieval_profiles
        self._profiles = profiles
        self._targets = targets

    def execute(self, request: CreateRetrievalProfileRequest) -> RetrievalProfile:
        """Create the profile after proving the profile/target pair is coherent.

        Raises:
            EmbeddingProfileNotFound: When the embedding profile is unknown.
            RetrievalProfileBlocked: When the target does not match the profile.
        """

        profile = self._profiles.get(request.embedding_profile_id)
        try:
            target = self._targets.get(request.indexing_target_id)
        except LookupError as error:
            raise RetrievalProfileBlocked(
                f"indexing target {request.indexing_target_id} does not exist"
            ) from error
        if target.vector_table != profile.vector_table or not target.accepts_metric(
            profile.distance_metric
        ):
            raise RetrievalProfileBlocked(
                "indexing target is not compatible with the embedding profile"
            )
        return self._retrieval_profiles.upsert(
            RetrievalProfile.build(
                project_id=request.project_id,
                consumer_scope_type=request.consumer_scope_type,
                consumer_scope_id=request.consumer_scope_id,
                corpus_version=request.corpus_version,
                embedding_profile_id=request.embedding_profile_id,
                indexing_target_id=request.indexing_target_id,
                lexical_fallback_policy=request.lexical_fallback_policy,
            )
        )


class RetrievalReadinessEvaluator:
    """Evaluate every precondition retrieval needs before answering."""

    def __init__(
        self,
        *,
        retrieval_profiles: RetrievalProfileRepository,
        profiles: EmbeddingProfileRepository,
        targets: IndexingTargetRepository,
        vector_search: VectorSearchPort,
        query_embedding: QueryEmbeddingService,
    ) -> None:
        self._retrieval_profiles = retrieval_profiles
        self._profiles = profiles
        self._targets = targets
        self._vector_search = vector_search
        self._query_embedding = query_embedding

    def evaluate(self, retrieval_profile_id: str) -> RetrievalReadiness:
        """Return the readiness verdict and every blocking reason."""

        retrieval_profile = self._retrieval_profiles.get(retrieval_profile_id)
        reasons: list[str] = []
        if not retrieval_profile.active:
            reasons.append("RETRIEVAL_PROFILE_BLOCKED")
        if retrieval_profile.validation_status != "passed":
            reasons.append("RETRIEVAL_PROFILE_NOT_VALIDATED")

        profile = self._profiles.get(retrieval_profile.embedding_profile_id)
        if not profile.can_embed_queries:
            reasons.append("EMBEDDING_PROFILE_COMPATIBILITY_NOT_PROVEN")

        active_rows = 0
        active_documents = 0
        bundle_id: str | None = None
        try:
            target = self._targets.get(retrieval_profile.indexing_target_id)
        except LookupError:
            reasons.append("INDEXING_TARGET_INCOMPATIBLE")
        else:
            if target.vector_table != profile.vector_table or not target.accepts_metric(
                profile.distance_metric
            ):
                reasons.append("INDEXING_TARGET_INCOMPATIBLE")
            active_rows = self._vector_search.count_active_rows(
                project_id=retrieval_profile.project_id,
                vector_table=target.vector_table,
                embedding_profile_id=profile.profile_id,
                indexing_target_id=target.indexing_target_id,
                corpus_version=retrieval_profile.corpus_version,
            )
            active_documents = self._vector_search.count_active_documents(
                project_id=retrieval_profile.project_id,
                vector_table=target.vector_table,
                embedding_profile_id=profile.profile_id,
                indexing_target_id=target.indexing_target_id,
                corpus_version=retrieval_profile.corpus_version,
            )
            if active_rows == 0:
                reasons.append("NO_ACTIVE_VECTOR_ROWS")
            bundles = self._vector_search.active_bundle_ids(
                project_id=retrieval_profile.project_id,
                vector_table=target.vector_table,
                embedding_profile_id=profile.profile_id,
                indexing_target_id=target.indexing_target_id,
                corpus_version=retrieval_profile.corpus_version,
            )
            bundle_id = bundles[0] if len(bundles) == 1 else None

        try:
            self._query_embedding.resolve_profile(retrieval_profile)
        except (RetrievalProfileBlocked, EmbeddingDomainError) as error:
            reasons.append(getattr(error, "code", "RETRIEVAL_PROFILE_BLOCKED"))

        return RetrievalReadiness(
            retrieval_profile_id=retrieval_profile_id,
            ready=not reasons,
            active_vector_rows=active_rows,
            active_document_count=active_documents,
            embedding_bundle_id=bundle_id,
            blocking_reasons=sorted(set(reasons)),
        )


class ActivateRetrievalProfileUseCase:
    """Activate one retrieval profile only after readiness passes."""

    def __init__(
        self,
        *,
        retrieval_profiles: RetrievalProfileRepository,
        readiness: RetrievalReadinessEvaluator,
        readiness_checks: ReadinessCheckRepository,
    ) -> None:
        self._retrieval_profiles = retrieval_profiles
        self._readiness = readiness
        self._readiness_checks = readiness_checks

    def execute(self, retrieval_profile_id: str) -> RetrievalProfile:
        """Activate one profile.

        Raises:
            RetrievalProfileBlocked: When any readiness precondition fails.
        """

        profile = self._retrieval_profiles.get(retrieval_profile_id)
        provisional = self._retrieval_profiles.upsert(
            profile.model_copy(update={"validation_status": "passed", "active": True})
        )
        readiness = self._readiness.evaluate(retrieval_profile_id)
        report: dict[str, object] = {
            "blocking_reasons": readiness.blocking_reasons,
            "active_vector_rows": readiness.active_vector_rows,
        }
        self._readiness_checks.record(
            ReadinessCheck(
                check_id=ReadinessCheck.deterministic_id(
                    check_kind="retrieval_readiness",
                    subject_id=retrieval_profile_id,
                    report=report,
                ),
                check_kind="retrieval_readiness",
                subject_id=retrieval_profile_id,
                embedding_profile_id=provisional.embedding_profile_id,
                indexing_target_id=provisional.indexing_target_id,
                status="passed" if readiness.ready else "blocked",
                validator_version=RETRIEVAL_VALIDATOR_VERSION,
                report=report,
            )
        )
        if not readiness.ready:
            self._retrieval_profiles.upsert(
                profile.model_copy(update={"validation_status": "failed", "active": False})
            )
            raise RetrievalProfileBlocked(
                "retrieval profile is not ready: " + ",".join(readiness.blocking_reasons)
            )
        activated = self._retrieval_profiles.activate(
            retrieval_profile_id=retrieval_profile_id,
            validated_at=_now(),
        )
        emit_pipeline_event(
            logger=logger,
            domain=ObservabilityDomain.RETRIEVAL,
            event="retrieval_profile_activated",
            status=EventStatus.COMPLETED,
            message="Retrieval profile activated",
            profile_id=activated.embedding_profile_id,
            capability="retrieve",
            metrics={"active_vector_rows": readiness.active_vector_rows},
            attributes={
                "retrieval_profile_id": activated.retrieval_profile_id,
                "embedding_profile_id": activated.embedding_profile_id,
                "indexing_target_id": activated.indexing_target_id,
            },
        )
        return activated


class GetRetrievalProfileStatusUseCase:
    """Report the runtime status of one retrieval profile."""

    def __init__(
        self,
        *,
        retrieval_profiles: RetrievalProfileRepository,
        profiles: EmbeddingProfileRepository,
        registry_status: QueryEmbeddingService,
        readiness: RetrievalReadinessEvaluator,
    ) -> None:
        self._retrieval_profiles = retrieval_profiles
        self._profiles = profiles
        self._query_embedding = registry_status
        self._readiness = readiness

    def execute(self, retrieval_profile_id: str) -> dict[str, object]:
        """Return the profile, its runtime status and its readiness verdict."""

        retrieval_profile = self._retrieval_profiles.get(retrieval_profile_id)
        profile = self._profiles.get(retrieval_profile.embedding_profile_id)
        blocked_reason: str | None = None
        engine_available = True
        try:
            self._query_embedding.resolve_profile(retrieval_profile)
        except (RetrievalProfileBlocked, EmbeddingDomainError) as error:
            engine_available = False
            blocked_reason = getattr(error, "code", "RETRIEVAL_PROFILE_BLOCKED")
        readiness = self._readiness.evaluate(retrieval_profile_id)
        runtime = RetrievalRuntimeStatus(
            retrieval_profile_id=retrieval_profile_id,
            embedding_profile_id=profile.profile_id,
            indexing_target_id=retrieval_profile.indexing_target_id,
            query_engine_available=engine_available,
            engine_revision_observed=profile.model_revision,
            vector_retrieval_enabled=readiness.ready,
            lexical_fallback_allowed=retrieval_profile.lexical_fallback_policy != "never",
            blocked_reason=blocked_reason,
        )
        return {
            "profile": retrieval_profile.model_dump(mode="json"),
            "runtime": runtime.model_dump(),
            "readiness": readiness.model_dump(),
        }


class RetrievalSearchService:
    """Run one hybrid retrieval pass restricted to one active lane."""

    def __init__(
        self,
        *,
        retrieval_profiles: RetrievalProfileRepository,
        profiles: EmbeddingProfileRepository,
        targets: IndexingTargetRepository,
        query_embedding: QueryEmbeddingService,
        vector_search: VectorSearchPort,
        lexical_search: LexicalSearchPort,
        parent_expansion: ParentExpansionPort,
        reranker: RerankerPort | None = None,
    ) -> None:
        self._retrieval_profiles = retrieval_profiles
        self._profiles = profiles
        self._targets = targets
        self._query_embedding = query_embedding
        self._vector_search = vector_search
        self._lexical_search = lexical_search
        self._parent_expansion = parent_expansion
        self._reranker = reranker or NoOpReranker()

    def search(
        self,
        *,
        retrieval_profile: RetrievalProfile,
        query: str,
        top_k: int = 10,
    ) -> list[RetrievedEvidence]:
        """Return evidence for one query.

        Hybrid by default: vector and lexical lanes both feed a reciprocal-rank
        fusion, followed by content dedup (md/PDF twins) and a per-parent cap.
        ``lexical_fallback_policy`` only decides whether lexical may answer
        alone when vector retrieval is unavailable.

        Raises:
            RetrievalProfileBlocked: When the lane cannot serve the query and the
                fallback policy forbids answering lexically.
        """

        _t_resolve = time.perf_counter()  # PROFTMP
        profile = self._query_embedding.resolve_profile(retrieval_profile)
        target = self._targets.get(retrieval_profile.indexing_target_id)
        print(f"PROFTMP resolve_profile+target={1000*(time.perf_counter()-_t_resolve):.1f}ms")  # PROFTMP
        candidate_pool_size = _hybrid_candidate_pool_size(top_k)
        try:
            _t = time.perf_counter()  # PROFTMP
            embeddings = self._query_embedding.embed_queries(
                retrieval_profile=retrieval_profile,
                queries=[query],
            )
            print(f"PROFTMP embed_queries={1000*(time.perf_counter()-_t):.1f}ms")  # PROFTMP
            _t = time.perf_counter()  # PROFTMP
            vector_candidates = self._vector_search.search(
                project_id=retrieval_profile.project_id,
                vector_table=target.vector_table,
                embedding_profile_id=profile.profile_id,
                indexing_target_id=target.indexing_target_id,
                corpus_version=retrieval_profile.corpus_version,
                distance_metric=profile.distance_metric,
                query_embedding=embeddings[0].vector,
                top_k=candidate_pool_size,
            )
            print(f"PROFTMP vector_search={1000*(time.perf_counter()-_t):.1f}ms")  # PROFTMP
        except EmbeddingDomainError as error:
            return self._lexical_only(
                retrieval_profile=retrieval_profile,
                query=query,
                top_k=top_k,
                reason=error.code,
            )
        lexical_candidates: list[RetrievedEvidence] = []
        lexical_degraded_reason: str | None = None
        # Señal secundaria obligatoria en el hybrid sano. Si el FTS falla no
        # debe tumbar la búsqueda, pero sí dejar una degradación observable.
        _t = time.perf_counter()  # PROFTMP
        try:
            lexical_candidates = self._lexical_search.search(
                project_id=retrieval_profile.project_id,
                query=query,
                embedding_profile_id=retrieval_profile.embedding_profile_id,
                corpus_version=retrieval_profile.corpus_version,
                top_k=candidate_pool_size,
            )
            print(f"PROFTMP lexical_search={1000*(time.perf_counter()-_t):.1f}ms")  # PROFTMP
        except Exception as error:  # noqa: BLE001 - degradación controlada
            lexical_degraded_reason = "lexical_hybrid_unavailable"
            emit_pipeline_event(
                logger=logger,
                domain=ObservabilityDomain.RETRIEVAL,
                event="lexical_hybrid_unavailable",
                status=EventStatus.WARNING,
                message="Lexical hybrid signal failed; continuing vector-only",
                capability="retrieve",
                attributes={
                    "retrieval_profile_id": retrieval_profile.retrieval_profile_id,
                    "error": repr(error),
                },
            )
            self._retrieval_profiles.record_runtime_status(
                retrieval_profile_id=retrieval_profile.retrieval_profile_id,
                last_runtime_status="failed",
            )
        else:
            self._retrieval_profiles.record_runtime_status(
                retrieval_profile_id=retrieval_profile.retrieval_profile_id,
                last_runtime_status="ok",
            )

        candidates = self._fuse_and_dedup(
            vector_candidates=vector_candidates,
            lexical_candidates=lexical_candidates,
            query=query,
            top_k=top_k,
        )
        enriched = self._with_parents(
            candidates=candidates,
            project_id=retrieval_profile.project_id,
            embedding_profile_id=profile.profile_id,
            corpus_version=retrieval_profile.corpus_version,
        )
        if lexical_degraded_reason is not None:
            return self._annotate_runtime_metadata(
                enriched,
                retrieval_mode="vector_only_degraded",
                degraded_reason=lexical_degraded_reason,
            )
        return self._annotate_runtime_metadata(
            enriched,
            retrieval_mode="hybrid",
        )

    def _fuse_and_dedup(
        self,
        *,
        vector_candidates: list[RetrievedEvidence],
        lexical_candidates: list[RetrievedEvidence],
        query: str,
        top_k: int,
    ) -> list[RetrievedEvidence]:
        """Fusiona ambas lanes con RRF, aplica dedup, rerankea y corta a ``top_k``."""

        _t_fuse = time.perf_counter()  # PROFTMP
        evidence_by_node: dict[str, RetrievedEvidence] = {}
        ranked_lists: list[list[RetrievedCandidate]] = []
        for lane in (vector_candidates, lexical_candidates):
            if not lane:
                continue
            for evidence in lane:
                evidence_by_node.setdefault(evidence.node_id, evidence)
            ranked_lists.append(
                [
                    RetrievedCandidate(
                        node_id=evidence.node_id,
                        text=evidence.text,
                        score=evidence.score,
                        source=evidence.source,
                        metadata=dict(evidence.metadata),
                    )
                    for evidence in lane
                ]
            )
        if not ranked_lists:
            return []

        fused = vector_primary_hybrid_fusion(
            vector_candidates=ranked_lists[0] if ranked_lists else [],
            lexical_candidates=ranked_lists[1] if len(ranked_lists) > 1 else [],
        )

        fingerprints = [content_fingerprint(item.text) for item in fused]
        parent_ids = [
            evidence_by_node[item.node_id].parent_node_id for item in fused
        ]
        source_ranks = [
            format_source_rank(
                str(evidence_by_node[item.node_id].metadata.get("source_relpath"))
                if evidence_by_node[item.node_id].metadata.get("source_relpath") is not None
                else None
            )
            for item in fused
        ]
        slots, dropped, slot_to_merged = select_unique_slots(
            fingerprints=fingerprints,
            parent_ids=parent_ids,
            source_ranks=source_ranks,
            max_per_parent=_MAX_CHILDREN_PER_PARENT,
            texts=[item.text for item in fused],
        )

        selected: list[RetrievedEvidence] = []
        for position, (_slot, chosen_index) in enumerate(slots):
            winner = fused[chosen_index]
            base = evidence_by_node[winner.node_id]
            merged_indices = slot_to_merged.get(_slot, [chosen_index])
            merged_sources: list[str] = []
            for mi in merged_indices:
                for src in fused[mi].metadata.get("retrieval_sources", []):
                    if src not in merged_sources:
                        merged_sources.append(src)
            selected.append(
                base.model_copy(
                    update={
                        "score": winner.score,
                        "metadata": {
                            **base.metadata,
                            "original_score": base.score,
                            "fusion_score": winner.score,
                            "fusion_sources": merged_sources or [base.source],
                            "fusion_position": position + 1,
                        },
                    }
                )
            )
        if selected and dropped:
            first = selected[0]
            selected[0] = first.model_copy(
                update={
                    "metadata": {
                        **first.metadata,
                        "dedup_dropped_count": dropped,
                    }
                }
            )
        rerank_pool = selected[: max(top_k, _RERANK_POOL_SIZE)]
        print(f"PROFTMP fuse+dedup={1000*(time.perf_counter()-_t_fuse):.1f}ms pool={len(rerank_pool)}")  # PROFTMP
        _t_rerank = time.perf_counter()  # PROFTMP
        result = self._reranker.rerank(query=query, candidates=rerank_pool, top_n=top_k)
        print(f"PROFTMP rerank={1000*(time.perf_counter()-_t_rerank):.1f}ms")  # PROFTMP
        return result

    def _lexical_only(
        self,
        *,
        retrieval_profile: RetrievalProfile,
        query: str,
        top_k: int,
        reason: str,
    ) -> list[RetrievedEvidence]:
        if retrieval_profile.lexical_fallback_policy == "never":
            self._retrieval_profiles.record_runtime_status(
                retrieval_profile_id=retrieval_profile.retrieval_profile_id,
                last_runtime_status="blocked",
            )
            raise LexicalFallbackNotAllowed(
                f"vector retrieval is blocked ({reason}) and lexical fallback is not allowed"
            )
        emit_pipeline_event(
            logger=logger,
            domain=ObservabilityDomain.RETRIEVAL,
            event="retrieval_lexical_fallback_used",
            status=EventStatus.WARNING,
            message="Vector retrieval blocked; lexical fallback used",
            capability="retrieve",
            attributes={
                "retrieval_profile_id": retrieval_profile.retrieval_profile_id,
                "blocked_reason": reason,
                "lexical_fallback_policy": retrieval_profile.lexical_fallback_policy,
            },
        )
        candidates = self._lexical_search.search(
            project_id=retrieval_profile.project_id,
            query=query,
            embedding_profile_id=retrieval_profile.embedding_profile_id,
            corpus_version=retrieval_profile.corpus_version,
            top_k=top_k,
        )
        self._retrieval_profiles.record_runtime_status(
            retrieval_profile_id=retrieval_profile.retrieval_profile_id,
            last_runtime_status="failed",
        )
        enriched = self._with_parents(
            candidates=candidates,
            project_id=retrieval_profile.project_id,
            embedding_profile_id=retrieval_profile.embedding_profile_id,
            corpus_version=retrieval_profile.corpus_version,
        )
        return self._annotate_runtime_metadata(
            enriched,
            retrieval_mode="lexical_fallback",
        )

    def _annotate_runtime_metadata(
        self,
        candidates: Sequence[RetrievedEvidence],
        *,
        retrieval_mode: str,
        degraded_reason: str | None = None,
    ) -> list[RetrievedEvidence]:
        annotated: list[RetrievedEvidence] = []
        for candidate in candidates:
            metadata = {
                **candidate.metadata,
                "retrieval_mode": retrieval_mode,
            }
            if degraded_reason is not None:
                metadata["degraded_reason"] = degraded_reason
            annotated.append(candidate.model_copy(update={"metadata": metadata}))
        return annotated

    def _with_parents(
        self,
        *,
        candidates: Sequence[RetrievedEvidence],
        project_id: str,
        embedding_profile_id: str,
        corpus_version: str,
    ) -> list[RetrievedEvidence]:
        parent_ids = [
            candidate.parent_node_id
            for candidate in candidates
            if candidate.parent_node_id is not None
        ]
        if not parent_ids:
            return list(candidates)
        _t_parents = time.perf_counter()  # PROFTMP
        parents = self._parent_expansion.expand(
            project_id=project_id,
            parent_node_ids=parent_ids,
            embedding_profile_id=embedding_profile_id,
            corpus_version=corpus_version,
        )
        print(f"PROFTMP parent_expansion={1000*(time.perf_counter()-_t_parents):.1f}ms n={len(parent_ids)}")  # PROFTMP
        enriched: list[RetrievedEvidence] = []
        for candidate in candidates:
            parent = parents.get(str(candidate.parent_node_id))
            if parent is None:
                enriched.append(candidate)
                continue
            enriched.append(
                candidate.model_copy(
                    update={
                        "page_start": (
                            candidate.page_start
                            if candidate.page_start is not None
                            else parent.page_start
                        ),
                        "page_end": (
                            candidate.page_end
                            if candidate.page_end is not None
                            else parent.page_end
                        ),
                        "section_title": candidate.section_title or parent.section_title,
                        "section_path": candidate.section_path or parent.section_path,
                    }
                )
            )
        return enriched


class SearchRetrievalUseCase:
    """Resolve one retrieval profile and run one evidence search."""

    def __init__(
        self,
        *,
        retrieval_profiles: RetrievalProfileRepository,
        search: RetrievalSearchService,
    ) -> None:
        self._retrieval_profiles = retrieval_profiles
        self._search = search

    def execute(self, request: SearchRetrievalRequest) -> list[RetrievedEvidence]:
        retrieval_profile = self._retrieval_profiles.get(request.retrieval_profile_id)
        return self._search.search(
            retrieval_profile=retrieval_profile,
            query=request.query,
            top_k=request.top_k,
        )


class ValidateRetrievalUseCase:
    """Run a controlled smoke validation without storing a real user question."""

    def __init__(
        self,
        *,
        retrieval_profiles: RetrievalProfileRepository,
        search: RetrievalSearchService,
        readiness_checks: ReadinessCheckRepository,
    ) -> None:
        self._retrieval_profiles = retrieval_profiles
        self._search = search
        self._readiness_checks = readiness_checks

    def execute(self, retrieval_profile_id: str) -> RetrievalValidation:
        """Validate one profile with a synthetic query."""

        retrieval_profile = self._retrieval_profiles.get(retrieval_profile_id)
        blocking: list[str] = []
        candidates: list[RetrievedEvidence] = []
        try:
            candidates = self._search.search(
                retrieval_profile=retrieval_profile,
                query=SMOKE_VALIDATION_QUERY,
                top_k=3,
            )
        except (RetrievalProfileBlocked, EmbeddingDomainError) as error:
            blocking.append(getattr(error, "code", "RETRIEVAL_PROFILE_BLOCKED"))

        status = "passed" if not blocking and candidates else ("blocked" if blocking else "failed")
        report: dict[str, object] = {
            "query_kind": "synthetic_smoke",
            "candidates_found": len(candidates),
            "blocking_reasons": blocking,
        }
        self._readiness_checks.record(
            ReadinessCheck(
                check_id=ReadinessCheck.deterministic_id(
                    check_kind="retrieval_readiness",
                    subject_id=retrieval_profile_id,
                    report=report,
                ),
                check_kind="retrieval_readiness",
                subject_id=retrieval_profile_id,
                embedding_profile_id=retrieval_profile.embedding_profile_id,
                indexing_target_id=retrieval_profile.indexing_target_id,
                status="passed" if status == "passed" else "blocked",
                validator_version=RETRIEVAL_VALIDATOR_VERSION,
                report=report,
            )
        )
        emit_pipeline_event(
            logger=logger,
            domain=ObservabilityDomain.RETRIEVAL,
            event="retrieval_validation_completed",
            status=EventStatus.COMPLETED if status == "passed" else EventStatus.BLOCKED,
            message="Retrieval validation completed",
            profile_id=retrieval_profile.embedding_profile_id,
            capability="retrieve",
            metrics={"candidates_found": len(candidates)},
            attributes={
                "retrieval_profile_id": retrieval_profile_id,
                "validation_status": status,
            },
        )
        return RetrievalValidation(
            retrieval_profile_id=retrieval_profile_id,
            status=status,  # type: ignore[arg-type]
            candidates_found=len(candidates),
            blocking_reasons=blocking,
        )
