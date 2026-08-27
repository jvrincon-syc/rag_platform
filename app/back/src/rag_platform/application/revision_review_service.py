"""Decisión operacional de revisión de documentos (Task 3, parity plan 2026-08-25).

Separa la decisión de elegibilidad (``Aprobar``/``Rechazar`` en la GUI legacy) de
la membresía en un corpus snapshot: ``CreateCorpusSnapshotUseCase`` rechaza una
decisión ``blocked`` porque un snapshot releaseable nunca contiene una revisión
bloqueada. Este caso de uso persiste la decisión igual, para que quede auditable
y visible en el read-model de documentos sin forzarla dentro de un snapshot.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from rag_platform.application.context import (
    PlatformAccessPolicy,
    RevisionReviewDecisionRecord,
    RevisionReviewDecisionRepository,
    SourceDocumentRepository,
)
from rag_platform.application.platform_access import (
    PlatformActor,
    require_project_operator,
)
from rag_platform.domain.errors import InvalidReviewDecision, RevisionProjectMismatch
from rag_platform.domain.identity import PlatformId
from rag_platform.domain.models import EligibilityDecision


class SubmitRevisionReviewDecisionUseCase:
    """Registra la decisión de elegibilidad de una revisión (fail-closed)."""

    def __init__(
        self,
        *,
        documents: SourceDocumentRepository,
        decisions: RevisionReviewDecisionRepository,
        access_policy: PlatformAccessPolicy,
        decision_id_factory: Callable[[], str],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._documents = documents
        self._decisions = decisions
        self._access_policy = access_policy
        self._decision_id_factory = decision_id_factory
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def execute(
        self,
        *,
        project_id: PlatformId,
        source_document_revision_id: PlatformId,
        decision: EligibilityDecision,
        reason: str,
        actor: PlatformActor,
    ) -> RevisionReviewDecisionRecord:
        require_project_operator(
            policy=self._access_policy, actor=actor, project_id=project_id
        )
        cleaned_reason = reason.strip()
        if not cleaned_reason:
            raise InvalidReviewDecision("reason is required")

        revision = self._documents.get_revision(source_document_revision_id)
        if revision.project_id != project_id:
            raise RevisionProjectMismatch(source_document_revision_id.value)

        if decision is EligibilityDecision.NOT_REQUIRED:
            raise InvalidReviewDecision(
                "not_required is derived server-side and cannot be submitted"
            )

        return self._decisions.add(
            RevisionReviewDecisionRecord(
                decision_id=self._decision_id_factory(),
                project_id=project_id.value,
                source_document_revision_id=source_document_revision_id.value,
                eligibility_decision=decision,
                reason=cleaned_reason,
                decided_by=actor.actor_id,
                decided_at=self._clock(),
            )
        )
