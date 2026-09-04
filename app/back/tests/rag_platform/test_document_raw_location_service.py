"""PR-1 1.7 — citas project-aware: resolución de raw por revisión, autorizada."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from rag_platform.application.document_raw_location_service import (
    GetProjectDocumentRevisionRawLocationUseCase,
)
from rag_platform.application.platform_access import PlatformActor
from rag_platform.domain.errors import PlatformAccessDenied, RevisionProjectMismatch
from rag_platform.domain.identity import IdentityKind, PlatformId
from rag_platform.domain.models import RevisionReviewState, SourceDocumentRevision
from rag_platform.infrastructure.in_memory.repositories import AllowAllAccessPolicy

PROJECT_A = PlatformId(kind=IdentityKind.PROJECT, value="proj_alpha")
PROJECT_B = PlatformId(kind=IdentityKind.PROJECT, value="proj_beta")
REVISION_ID = PlatformId(
    kind=IdentityKind.SOURCE_DOCUMENT_REVISION, value="srev_abc123"
)


def _revision(project_id: PlatformId, source_relpath: str = "manuals/x.pdf") -> SourceDocumentRevision:
    return SourceDocumentRevision(
        source_document_revision_id=REVISION_ID,
        logical_document_id=PlatformId(kind=IdentityKind.SOURCE_DOCUMENT, value="sdoc_abc"),
        project_id=project_id,
        source_relpath=source_relpath,
        raw_content_hash="a" * 64,
        file_size=10,
        uploaded_by="op-1",
        uploaded_at=datetime.now(timezone.utc),
        review_state=RevisionReviewState.PROCESSED,
    )


class _FakeSourceDocumentRepository:
    """Fake determinístico: solo implementa lo que el caso de uso llama."""

    def __init__(self, revision: SourceDocumentRevision) -> None:
        self._revision = revision

    def get_revision(self, source_document_revision_id: PlatformId) -> SourceDocumentRevision:
        assert source_document_revision_id == REVISION_ID
        return self._revision


class _FakeProjectRepository:
    def __init__(self) -> None:
        self.requested: list[PlatformId] = []

    def get(self, project_id: PlatformId) -> object:
        self.requested.append(project_id)
        return object()  # placeholder; el fake raw_storage no inspecciona el proyecto


class _FakeProjectRawStorage:
    def __init__(self, raw_root: Path) -> None:
        self._raw_root = raw_root
        self.resolved_for: list[object] = []

    def write_raw_bytes(self, project: object, source_relpath: str, content: bytes) -> None:
        raise NotImplementedError("not exercised by this use case")

    def resolve_raw_root(self, project: object) -> Path:
        self.resolved_for.append(project)
        return self._raw_root


def _use_case(
    *, revision: SourceDocumentRevision, raw_root: Path
) -> tuple[GetProjectDocumentRevisionRawLocationUseCase, _FakeProjectRepository, _FakeProjectRawStorage]:
    projects = _FakeProjectRepository()
    raw_storage = _FakeProjectRawStorage(raw_root)
    use_case = GetProjectDocumentRevisionRawLocationUseCase(
        projects=projects,
        documents=_FakeSourceDocumentRepository(revision),
        raw_storage=raw_storage,
        access_policy=AllowAllAccessPolicy(),
    )
    return use_case, projects, raw_storage


def test_resuelve_ubicacion_cuando_revision_pertenece_al_proyecto(tmp_path: Path) -> None:
    revision = _revision(PROJECT_A, source_relpath="manuals/guia.pdf")
    use_case, projects, raw_storage = _use_case(revision=revision, raw_root=tmp_path)

    location = use_case.execute(
        project_id=PROJECT_A,
        source_document_revision_id=REVISION_ID,
        actor=PlatformActor(actor_id="op-1"),
    )

    assert location.raw_root == tmp_path
    assert location.source_relpath == "manuals/guia.pdf"
    assert projects.requested == [PROJECT_A]
    assert len(raw_storage.resolved_for) == 1


def test_rechaza_revision_de_otro_proyecto(tmp_path: Path) -> None:
    revision = _revision(PROJECT_B)  # la revisión pertenece a B
    use_case, projects, raw_storage = _use_case(revision=revision, raw_root=tmp_path)

    with pytest.raises(RevisionProjectMismatch):
        use_case.execute(
            project_id=PROJECT_A,  # se pide desde A
            source_document_revision_id=REVISION_ID,
            actor=PlatformActor(actor_id="op-1"),
        )

    # Fail-closed antes de tocar el proyecto o resolver la raíz física.
    assert projects.requested == []
    assert raw_storage.resolved_for == []


def test_rechaza_actor_fuera_de_scope_de_proyecto(tmp_path: Path) -> None:
    revision = _revision(PROJECT_A)
    use_case, projects, raw_storage = _use_case(revision=revision, raw_root=tmp_path)
    scoped_actor = PlatformActor(actor_id="op-1", project_scope=(PROJECT_B.value,))

    with pytest.raises(PlatformAccessDenied):
        use_case.execute(
            project_id=PROJECT_A,
            source_document_revision_id=REVISION_ID,
            actor=scoped_actor,
        )

    assert projects.requested == []
    assert raw_storage.resolved_for == []
