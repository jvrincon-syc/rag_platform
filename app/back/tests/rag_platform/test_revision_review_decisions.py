"""Contrato de aplicación de la decisión operacional de revisión (Task 3).

Cubre ``SubmitRevisionReviewDecisionUseCase``: una decisión ``blocked`` se
persiste igual (sin exigir que la revisión entre a un snapshot), ``reason`` es
obligatorio, y una revisión de otro proyecto falla cerrado.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from rag_platform.application.platform_access import PlatformActor
from rag_platform.application.revision_review_service import (
    SubmitRevisionReviewDecisionUseCase,
)
from rag_platform.domain.errors import InvalidReviewDecision, RevisionProjectMismatch
from rag_platform.domain.identity import IdentityKind, PlatformId
from rag_platform.domain.models import (
    EligibilityDecision,
    RevisionReviewState,
    SourceDocument,
    SourceDocumentRevision,
)
from rag_platform.infrastructure.in_memory.repositories import (
    AllowAllAccessPolicy,
    InMemoryRevisionReviewDecisionRepository,
    InMemorySourceDocumentRepository,
)


def _pid(kind: IdentityKind, value: str) -> PlatformId:
    return PlatformId(kind=kind, value=value)


def _seed_revision(
    documents: InMemorySourceDocumentRepository,
    *,
    project_id: str = "proj_sst-general",
    revision_id: str = "srev_manual",
    review_state: RevisionReviewState = RevisionReviewState.NEEDS_REVIEW,
) -> None:
    logical_id = _pid(IdentityKind.SOURCE_DOCUMENT, "sdoc_manual")
    project_pid = _pid(IdentityKind.PROJECT, project_id)
    documents.upsert_document(
        SourceDocument(
            logical_document_id=logical_id,
            project_id=project_pid,
            source_relpath="manuales/manual.pdf",
            created_at=datetime(2026, 8, 25, tzinfo=timezone.utc),
        )
    )
    documents.add_revision(
        SourceDocumentRevision(
            source_document_revision_id=_pid(
                IdentityKind.SOURCE_DOCUMENT_REVISION,
                revision_id,
            ),
            logical_document_id=logical_id,
            project_id=project_pid,
            source_relpath="manuales/manual.pdf",
            raw_content_hash="a" * 64,
            file_size=42,
            uploaded_by="operator-1",
            uploaded_at=datetime(2026, 8, 25, tzinfo=timezone.utc),
            review_state=review_state,
        )
    )


def _use_case():
    documents = InMemorySourceDocumentRepository()
    decisions = InMemoryRevisionReviewDecisionRepository()
    use_case = SubmitRevisionReviewDecisionUseCase(
        documents=documents,
        decisions=decisions,
        access_policy=AllowAllAccessPolicy(),
        decision_id_factory=lambda: "rrd_001",
        clock=lambda: datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc),
    )
    return use_case, documents, decisions


def test_submit_reject_persists_blocked_without_snapshot_membership() -> None:
    use_case, documents, decisions = _use_case()
    _seed_revision(documents)

    record = use_case.execute(
        project_id=_pid(IdentityKind.PROJECT, "proj_sst-general"),
        source_document_revision_id=_pid(
            IdentityKind.SOURCE_DOCUMENT_REVISION,
            "srev_manual",
        ),
        decision=EligibilityDecision.BLOCKED,
        reason="OCR incompleto; no apto para publicar.",
        actor=PlatformActor(actor_id="operator-1"),
    )

    assert record.project_id == "proj_sst-general"
    assert record.source_document_revision_id == "srev_manual"
    assert record.eligibility_decision is EligibilityDecision.BLOCKED
    latest = decisions.latest_for_project(_pid(IdentityKind.PROJECT, "proj_sst-general"))
    assert latest["srev_manual"].eligibility_decision is EligibilityDecision.BLOCKED


def test_submit_approve_persists_approved_after_review() -> None:
    use_case, documents, decisions = _use_case()
    _seed_revision(documents)

    record = use_case.execute(
        project_id=_pid(IdentityKind.PROJECT, "proj_sst-general"),
        source_document_revision_id=_pid(
            IdentityKind.SOURCE_DOCUMENT_REVISION,
            "srev_manual",
        ),
        decision=EligibilityDecision.APPROVED_AFTER_REVIEW,
        reason="Revision humana completada.",
        actor=PlatformActor(actor_id="operator-1"),
    )

    assert record.eligibility_decision is EligibilityDecision.APPROVED_AFTER_REVIEW
    latest = decisions.latest_for_project(_pid(IdentityKind.PROJECT, "proj_sst-general"))
    assert latest["srev_manual"].reason == "Revision humana completada."


def test_submit_review_decision_rejects_cross_project_revision() -> None:
    use_case, documents, _ = _use_case()
    _seed_revision(documents, project_id="proj_otro")

    with pytest.raises(RevisionProjectMismatch):
        use_case.execute(
            project_id=_pid(IdentityKind.PROJECT, "proj_sst-general"),
            source_document_revision_id=_pid(
                IdentityKind.SOURCE_DOCUMENT_REVISION,
                "srev_manual",
            ),
            decision=EligibilityDecision.BLOCKED,
            reason="No pertenece al proyecto.",
            actor=PlatformActor(actor_id="operator-1"),
        )


def test_submit_review_decision_requires_reason() -> None:
    use_case, documents, _ = _use_case()
    _seed_revision(documents)

    with pytest.raises(InvalidReviewDecision, match="reason is required"):
        use_case.execute(
            project_id=_pid(IdentityKind.PROJECT, "proj_sst-general"),
            source_document_revision_id=_pid(
                IdentityKind.SOURCE_DOCUMENT_REVISION,
                "srev_manual",
            ),
            decision=EligibilityDecision.BLOCKED,
            reason=" ",
            actor=PlatformActor(actor_id="operator-1"),
        )
