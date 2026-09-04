"""Resuelve la ubicación física del raw de una revisión (PR-1 1.7 — citas project-aware).

Antes, ``chatbot/api/raw_documents.py`` servía ``/api/documents/raw/{file_path}``
bajo una raíz global (``SST_RAW_DOCS_ROOT``), sin ``project_id`` ni verificación
de pertenencia: dos proyectos con el mismo ``source_relpath`` colisionaban en la
misma URL y cualquier actor autenticado podía leer el raw de cualquier proyecto
con solo conocer la ruta.

Este caso de uso resuelve la revisión por su identidad, exige que el actor esté
autorizado sobre el ``project_id`` del path (``require_project_operator``) y
verifica que la revisión pertenezca a ese mismo proyecto (``RevisionProjectMismatch``
si no — el mismo error de dominio que ya usa ``revision_review_service`` para esta
invariante, fail-closed). La raíz física la resuelve el puerto ``ProjectRawStorage``
(misma autoridad catalog-driven que el upload); este caso de uso no lee bytes ni
valida contención de ``source_relpath`` — eso lo hace el router, igual que la ruta
legacy.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rag_platform.application.context import (
    PlatformAccessPolicy,
    ProjectRawStorage,
    ProjectRepository,
    SourceDocumentRepository,
)
from rag_platform.application.platform_access import (
    PlatformActor,
    require_project_operator,
)
from rag_platform.domain.errors import RevisionProjectMismatch
from rag_platform.domain.identity import PlatformId


@dataclass(frozen=True)
class DocumentRevisionRawLocation:
    """Ubicación física resuelta y autorizada del raw de una revisión."""

    raw_root: Path
    source_relpath: str


class GetProjectDocumentRevisionRawLocationUseCase:
    """Resuelve raíz + relpath del raw de una revisión, project-scoped y fail-closed."""

    def __init__(
        self,
        *,
        projects: ProjectRepository,
        documents: SourceDocumentRepository,
        raw_storage: ProjectRawStorage,
        access_policy: PlatformAccessPolicy,
    ) -> None:
        self._projects = projects
        self._documents = documents
        self._raw_storage = raw_storage
        self._access_policy = access_policy

    def execute(
        self,
        *,
        project_id: PlatformId,
        source_document_revision_id: PlatformId,
        actor: PlatformActor,
    ) -> DocumentRevisionRawLocation:
        """Devuelve la ubicación física del raw, o falla cerrado.

        Args:
            project_id: Proyecto del que el actor pide el documento (del path HTTP).
            source_document_revision_id: Revisión inmutable a servir.
            actor: Actor autenticado; su scope se valida contra ``project_id``.

        Raises:
            PlatformAccessDenied: Si el actor no es operador o no tiene scope
                sobre ``project_id``.
            SourceDocumentRevisionNotFound: Si la revisión no está registrada.
            RevisionProjectMismatch: Si la revisión pertenece a otro proyecto —
                nunca se filtra la ubicación de un documento ajeno.
        """

        require_project_operator(
            policy=self._access_policy, actor=actor, project_id=project_id
        )
        revision = self._documents.get_revision(source_document_revision_id)
        if revision.project_id != project_id:
            raise RevisionProjectMismatch(source_document_revision_id.value)
        project = self._projects.get(project_id)
        raw_root = self._raw_storage.resolve_raw_root(project)
        return DocumentRevisionRawLocation(
            raw_root=raw_root, source_relpath=revision.source_relpath
        )
