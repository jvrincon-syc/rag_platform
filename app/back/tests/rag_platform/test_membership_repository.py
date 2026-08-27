"""Contrato de inserción de ``rag_release_memberships``.

El INSERT es deliberadamente plano: un duplicado (misma release+revision u
ordinal) es una anomalía que debe fallar cerrado con ``UniqueViolation``, no
silenciarse con ``ON CONFLICT`` — eso ocultaría drift entre artefactos
re-resueltos. El E2E live garantiza estado limpio entre intentos; una futura
reanudación de builds deberá comparar artefactos y fallar ante diferencias.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rag_platform.domain.identity import IdentityKind, PlatformId
from rag_platform.domain.lifecycle import RagReleaseMembership
from rag_platform.infrastructure.in_memory.release_repositories import (
    InMemoryRagReleaseMembershipRepository,
)
from rag_platform.infrastructure.postgres.release_repositories import (
    PostgresRagReleaseMembershipRepository,
)


def _membership(ordinal: int = 3) -> RagReleaseMembership:
    return RagReleaseMembership(
        rag_release_id=PlatformId(kind=IdentityKind.RAG_RELEASE, value="ragr_test0001"),
        project_id=PlatformId(kind=IdentityKind.PROJECT, value="proj_test"),
        ordinal=ordinal,
        source_document_revision_id=PlatformId(
            kind=IdentityKind.SOURCE_DOCUMENT_REVISION, value="srev_test0001"
        ),
        normalized_document_id="nd-1",
        chunk_bundle_id="cb-1",
        embedding_bundle_id="eb-1",
        materialization_id="im-1",
    )


@dataclass
class _RecordingCursor:
    statements: list[str] = field(default_factory=list)

    def execute(self, statement: str, params: object = None) -> None:
        self.statements.append(statement)

    def __enter__(self) -> "_RecordingCursor":
        return self

    def __exit__(self, *_exc_info: object) -> bool:
        return False


@dataclass
class _RecordingConnection:
    cursor_obj: _RecordingCursor = field(default_factory=_RecordingCursor)

    def cursor(self) -> _RecordingCursor:
        return self.cursor_obj


def test_add_postgres_no_silencia_duplicados() -> None:
    connection = _RecordingConnection()
    repository = PostgresRagReleaseMembershipRepository(connection)

    repository.add(_membership())

    statement = connection.cursor_obj.statements[-1]
    assert "INSERT INTO rag_release_memberships" in statement
    assert "ON CONFLICT" not in statement, (
        "un conflicto de identidad debe explotar como UniqueViolation;"
        " ON CONFLICT ocultaria drift entre artefactos re-resueltos"
    )


def test_add_in_memory_sobreescribe_por_revision_sin_duplicar() -> None:
    repository = InMemoryRagReleaseMembershipRepository()

    repository.add(_membership(ordinal=3))
    repository.add(_membership(ordinal=3))

    release_id = PlatformId(kind=IdentityKind.RAG_RELEASE, value="ragr_test0001")
    memberships = repository.list_for_release(release_id)
    assert len(memberships) == 1
    assert memberships[0].ordinal == 3
