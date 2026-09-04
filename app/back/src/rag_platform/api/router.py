"""Rutas HTTP de la plataforma RAG multi-proyecto (Fase 7).

Adaptador HTTP **delgado** sobre ``services.rag_platform.*``: valida entrada
Pydantic, resuelve el actor de confianza server-side, aplica la guarda de
idempotencia donde corresponde y delega en el caso de uso ya cableado. El router
no ejecuta SQL, no calcula fingerprints, no resuelve tablas físicas ni deriva
``indexing_target_id``, y no importa repositorios concretos: toda esa autoridad
vive en la capa de aplicación.

La traducción de errores de dominio (``RagPlatformError``) al envelope HTTP es
**centralizada** en ``api/app.py`` (un solo ``exception_handler``); aquí no hay
``try/except RagPlatformError`` repetido por endpoint.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, Query, UploadFile, status

from core.api.http import (
    DEFAULT_PAGE_SIZE,
    ErrorEnvelopeSchema,
    MAX_PAGE_SIZE,
    RequestThrottle,
    http_error,
    paginate,
    rate_limit_error,
)
from rag_platform.api.dependencies import (
    get_actor_provider,
    get_idempotency_store,
    get_platform_services,
    require_rag_platform_enabled,
)
from rag_platform.api.schemas import (
    ChunkingProfileReadSchema,
    CorpusSnapshotSchema,
    CreateCorpusSnapshotRequestSchema,
    CreateProjectRequestSchema,
    CreateReleaseDraftRequestSchema,
    CreateVariantRequestSchema,
    NormalizeProjectDocumentsRequestSchema,
    PaginatedCorpusSnapshotsSchema,
    PaginatedProjectDocumentsSchema,
    PaginatedProjectsSchema,
    PaginatedReleasesSchema,
    PaginatedVariantsSchema,
    ProcessingProfileReadSchema,
    ProjectConfigurationSchema,
    ProjectDocumentRevisionSchema,
    ProjectNormalizeReportSchema,
    ProjectSchema,
    ProvisionCustomChunkingVariantRequestSchema,
    ProvisionDefaultVariantRequestSchema,
    ReleaseBuildAcceptedSchema,
    ReleaseBuildRequestSchema,
    ReleaseBuildStatusSchema,
    ReleaseSchema,
    RetireReleaseRequestSchema,
    RevisionReviewDecisionSchema,
    SubmitRevisionReviewDecisionRequestSchema,
    UpdateProjectConfigurationRequestSchema,
    UpdateProjectRequestSchema,
    VariantMatrixCellSchema,
    VariantSchema,
    build_job_to_status_schema,
    chunking_profile_to_schema,
    configuration_to_schema,
    document_row_to_schema,
    matrix_cell_to_schema,
    normalize_outcome_to_schema,
    processing_profile_to_schema,
    project_to_schema,
    release_to_schema,
    snapshot_to_schema,
    uploaded_revision_to_schema,
    variant_to_schema,
)
from rag_platform.application.actor_provider import TrustedPlatformActorProvider
from rag_platform.application.idempotency import IdempotencyGuard, IdempotencyStore
from rag_platform.application.platform_access import PlatformActor
from rag_platform.application.variant_matrix_service import platform_id_body
from rag_platform.application.project_service import CreateProjectRequest
from rag_platform.application.project_configuration_service import (
    UpdateProjectConfigurationRequest,
)
from rag_platform.application.services import RagPlatformServices
from rag_platform.domain.identity import IdentityKind, PlatformId
from rag_platform.domain.models import EligibilityDecision


router = APIRouter(
    prefix="/api/platform",
    tags=["platform"],
    dependencies=[Depends(require_rag_platform_enabled)],
    responses={
        400: {"model": ErrorEnvelopeSchema},
        403: {"model": ErrorEnvelopeSchema},
        404: {"model": ErrorEnvelopeSchema},
        409: {"model": ErrorEnvelopeSchema},
        422: {"model": ErrorEnvelopeSchema},
        429: {"model": ErrorEnvelopeSchema},
        503: {"model": ErrorEnvelopeSchema},
    },
)

#: Header de idempotencia obligatorio en mutaciones de release.
IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", min_length=1)]

#: PR-6: per-actor sliding-window throttle for release builds (reuses the
#: pattern of ``ingestion.gui.server.GuiRegisterThrottle``). A build enqueues a
#: real embedding/indexing job; conservative default protects against an actor
#: hammering the endpoint (idempotency already dedupes retries of the SAME
#: intent, this bounds distinct intents over time).
_BUILD_RATE_LIMIT_MAX_ATTEMPTS = int(
    os.environ.get("RELEASE_BUILD_RATE_LIMIT_MAX_ATTEMPTS", "5")
)
_BUILD_RATE_LIMIT_WINDOW_SECONDS = int(
    os.environ.get("RELEASE_BUILD_RATE_LIMIT_WINDOW_SECONDS", "3600")
)
_build_throttle = RequestThrottle(
    max_attempts=_BUILD_RATE_LIMIT_MAX_ATTEMPTS,
    window=timedelta(seconds=_BUILD_RATE_LIMIT_WINDOW_SECONDS),
)


def get_actor(
    provider: TrustedPlatformActorProvider = Depends(get_actor_provider),
) -> PlatformActor:
    """Resuelve el ``PlatformActor`` de confianza (fail-closed si no hay actor)."""

    return provider.current_actor()


def _rate_limit_release_build(actor: PlatformActor = Depends(get_actor)) -> None:
    """PR-6: rechaza cuando ``actor`` excede el límite de builds de release."""

    if not _build_throttle.allow(actor.actor_id):
        raise rate_limit_error(
            code="RELEASE_BUILD_RATE_LIMITED",
            message="too many release build requests from this actor",
            retry_after_seconds=_BUILD_RATE_LIMIT_WINDOW_SECONDS,
        )


def _parse_id(kind: IdentityKind, value: str) -> PlatformId:
    """Parsea un ID (path o body) a ``PlatformId``.

    Un ID malformado lanza ``InvalidIdentity``, traducida a 422 estable por el
    handler central de ``api/app.py`` (mismo punto que los IDs construidos dentro
    de los casos de uso desde slugs de body). Sin traducción duplicada aquí.
    """

    return PlatformId.parse(kind, value)


def _eligibility_decisions(
    raw: dict[str, str],
) -> dict[str, EligibilityDecision]:
    """Traduce las decisiones de elegibilidad del request o falla con 422."""

    decisions: dict[str, EligibilityDecision] = {}
    for revision_id, value in raw.items():
        try:
            decisions[revision_id] = EligibilityDecision(value)
        except ValueError as error:
            raise http_error(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                code="INVALID_ELIGIBILITY_DECISION",
                message=f"unknown eligibility decision {value!r}",
            ) from error
    return decisions


# --------------------------------------------------------------------------- #
# Proyectos                                                                    #
# --------------------------------------------------------------------------- #


@router.get("/projects", response_model=PaginatedProjectsSchema)
def list_projects(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> dict:
    items = [
        project_to_schema(p) for p in services.list_projects.execute(actor=actor)
    ]
    return paginate(items, page=page, page_size=page_size)


@router.post(
    "/projects",
    status_code=status.HTTP_201_CREATED,
    response_model=ProjectSchema,
)
def create_project(
    payload: CreateProjectRequestSchema,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> ProjectSchema:
    # El DTO HTTP no expone ``target_bindings`` (target físico): se provisionan
    # server-side, así que la petición de aplicación se arma con bindings vacíos.
    request = CreateProjectRequest(
        project_slug=payload.project_slug,
        display_name=payload.display_name,
        document_type_template=payload.document_type_template,
        corpus_organization_policy=payload.corpus_organization_policy,
        embedding_profiles=payload.embedding_profiles,
    )
    project = services.create_project.execute(request, actor=actor)
    return project_to_schema(project)


@router.post("/projects/{project_id}/provision-default-variant")
def provision_default_variant_endpoint(
    project_id: str,
    payload: ProvisionDefaultVariantRequestSchema,
    actor: PlatformActor = Depends(get_actor),
) -> dict:
    # Auto-provision del setup RAG por defecto (allowlist + binding + processing +
    # chunking + variante) para que un proyecto recien creado por la UI ingiera de una.
    # Idempotente y transaccional; `actor` (Depends) exige sesion autenticada.
    from rag_platform.infrastructure.default_provisioning import (
        provision_default_variant,
    )

    pid = _parse_id(IdentityKind.PROJECT, project_id)
    slug = pid.value[len("proj_") :] if pid.value.startswith("proj_") else pid.value
    try:
        return provision_default_variant(
            project_slug=slug, embedding_backend=payload.embedding_backend
        )
    except ValueError as error:
        raise http_error(
            status_code=422, code="PROVISION_DEFAULT_VARIANT_FAILED", message=str(error)
        )


@router.post("/projects/{project_id}/provision-custom-chunking-variant")
def provision_custom_chunking_variant_endpoint(
    project_id: str,
    payload: ProvisionCustomChunkingVariantRequestSchema,
    actor: PlatformActor = Depends(get_actor),
) -> dict:
    # Crea una variante con hiperparámetros de chunking a medida (child tokens +
    # overlap). Valida invariantes con el motor real antes de persistir; idempotente
    # (misma receta -> mismo perfil). `actor` (Depends) exige sesion autenticada.
    from rag_platform.infrastructure.default_provisioning import (
        provision_custom_chunking_variant,
    )

    pid = _parse_id(IdentityKind.PROJECT, project_id)
    slug = pid.value[len("proj_") :] if pid.value.startswith("proj_") else pid.value
    try:
        return provision_custom_chunking_variant(
            project_slug=slug,
            embedding_backend=payload.embedding_backend,
            chunking_params={
                "child_min_tokens": payload.child_min_tokens,
                "child_target_tokens": payload.child_target_tokens,
                "child_max_tokens": payload.child_max_tokens,
                "overlap_min_tokens": payload.overlap_min_tokens,
                "overlap_max_tokens": payload.overlap_max_tokens,
                "overlap_ratio": payload.overlap_ratio,
                "include_section_context": payload.include_section_context,
            },
        )
    except ValueError as error:
        raise http_error(
            status_code=422,
            code="PROVISION_CUSTOM_CHUNKING_FAILED",
            message=str(error),
        )


@router.get("/projects/{project_id}", response_model=ProjectSchema)
def get_project(
    project_id: str,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> ProjectSchema:
    project = services.get_project.execute(
        _parse_id(IdentityKind.PROJECT, project_id), actor=actor
    )
    return project_to_schema(project)


@router.patch("/projects/{project_id}", response_model=ProjectSchema)
def update_project(
    project_id: str,
    payload: UpdateProjectRequestSchema,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> ProjectSchema:
    project = services.update_project_metadata.execute(
        _parse_id(IdentityKind.PROJECT, project_id),
        display_name=payload.display_name,
        actor=actor,
    )
    return project_to_schema(project)


@router.get(
    "/projects/{project_id}/configuration",
    response_model=ProjectConfigurationSchema,
)
def get_project_configuration(
    project_id: str,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> ProjectConfigurationSchema:
    configuration = services.get_project_configuration.execute(
        _parse_id(IdentityKind.PROJECT, project_id), actor=actor
    )
    return configuration_to_schema(configuration)


@router.patch(
    "/projects/{project_id}/configuration",
    response_model=ProjectConfigurationSchema,
)
def update_project_configuration(
    project_id: str,
    payload: UpdateProjectConfigurationRequestSchema,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> ProjectConfigurationSchema:
    # ``target_bindings`` no cruza HTTP (no expone el target físico); el versionado
    # de bindings es server-side, así que la petición se arma con bindings vacíos.
    request = UpdateProjectConfigurationRequest(
        corpus_organization_policy=payload.corpus_organization_policy,
        document_types=payload.document_types,
        embedding_profiles=payload.embedding_profiles,
    )
    configuration = services.create_project_configuration_version.execute(
        _parse_id(IdentityKind.PROJECT, project_id),
        request=request,
        actor=actor,
    )
    return configuration_to_schema(configuration)


@router.get(
    "/projects/{project_id}/processing-profiles",
    response_model=list[ProcessingProfileReadSchema],
)
def list_processing_profiles(
    project_id: str,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> list[ProcessingProfileReadSchema]:
    profiles = services.list_processing_profiles.execute(
        _parse_id(IdentityKind.PROJECT, project_id), actor=actor
    )
    return [processing_profile_to_schema(p) for p in profiles]


@router.get(
    "/projects/{project_id}/chunking-profiles",
    response_model=list[ChunkingProfileReadSchema],
)
def list_chunking_profiles(
    project_id: str,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> list[ChunkingProfileReadSchema]:
    profiles = services.list_chunking_profiles.execute(
        _parse_id(IdentityKind.PROJECT, project_id), actor=actor
    )
    return [chunking_profile_to_schema(p) for p in profiles]


# --------------------------------------------------------------------------- #
# Variantes                                                                    #
# --------------------------------------------------------------------------- #


@router.get(
    "/projects/{project_id}/variant-matrix",
    response_model=list[VariantMatrixCellSchema],
)
def get_variant_matrix(
    project_id: str,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> list[VariantMatrixCellSchema]:
    cells = services.get_variant_matrix.execute(
        project_id=_parse_id(IdentityKind.PROJECT, project_id), actor=actor
    )
    return [matrix_cell_to_schema(cell) for cell in cells]


@router.get(
    "/projects/{project_id}/variants",
    response_model=PaginatedVariantsSchema,
)
def list_variants(
    project_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> dict:
    variants = services.list_project_variants.execute(
        _parse_id(IdentityKind.PROJECT, project_id), actor=actor
    )
    items = [variant_to_schema(v) for v in variants]
    return paginate(items, page=page, page_size=page_size)


@router.post(
    "/projects/{project_id}/variants",
    status_code=status.HTTP_201_CREATED,
    response_model=VariantSchema,
)
def create_variant(
    project_id: str,
    payload: CreateVariantRequestSchema,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> VariantSchema:
    variant = services.create_variant_from_matrix_cell.execute(
        project_id=_parse_id(IdentityKind.PROJECT, project_id),
        cell_id=payload.cell_id,
        variant_slug=payload.variant_slug,
        actor=actor,
    )
    return variant_to_schema(variant)


# --------------------------------------------------------------------------- #
# Documentos (intake project-aware)                                            #
# --------------------------------------------------------------------------- #


@router.get(
    "/projects/{project_id}/documents",
    response_model=PaginatedProjectDocumentsSchema,
)
def list_project_documents(
    project_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> dict:
    rows = services.list_project_documents.execute(
        _parse_id(IdentityKind.PROJECT, project_id), actor=actor
    )
    items = [document_row_to_schema(row) for row in rows]
    return paginate(items, page=page, page_size=page_size)


@router.post(
    "/projects/{project_id}/documents",
    status_code=status.HTTP_201_CREATED,
    response_model=ProjectDocumentRevisionSchema,
)
def upload_project_document(
    project_id: str,
    file: UploadFile = File(...),
    source_relpath: str = Form(..., min_length=1, max_length=1024),
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> ProjectDocumentRevisionSchema:
    # El servidor calcula hash/tamaño y persiste bytes server-side; el actor viene
    # del principal autenticado, nunca del form (invariante §Actor).
    content = file.file.read()
    revision = services.upload_project_document.execute(
        project_id=_parse_id(IdentityKind.PROJECT, project_id),
        source_relpath=source_relpath,
        content=content,
        actor=actor,
    )
    return uploaded_revision_to_schema(revision)


@router.post(
    "/projects/{project_id}/normalize",
    response_model=ProjectNormalizeReportSchema,
)
def normalize_project_documents(
    project_id: str,
    payload: NormalizeProjectDocumentsRequestSchema,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> ProjectNormalizeReportSchema:
    # Normalización síncrona reutilizando run_pipeline (on-prem por defecto). El
    # actor viene del principal; la variante ata el perfil de procesamiento.
    outcome = services.normalize_project_documents.execute(
        project_id=_parse_id(IdentityKind.PROJECT, project_id),
        rag_variant_id=_parse_id(IdentityKind.RAG_VARIANT, payload.rag_variant_id),
        document_revision_ids=payload.document_revision_ids,
        force=payload.force,
        actor=actor,
    )
    return normalize_outcome_to_schema(outcome)


@router.post(
    "/projects/{project_id}/document-revisions/{source_document_revision_id}/review-decision",
    response_model=RevisionReviewDecisionSchema,
)
def submit_revision_review_decision(
    project_id: str,
    source_document_revision_id: str,
    payload: SubmitRevisionReviewDecisionRequestSchema,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> RevisionReviewDecisionSchema:
    # Decisión operacional independiente de la membresía en un snapshot (Task 3):
    # `blocked` se persiste igual, sin forzar la revisión dentro de un snapshot.
    record = services.submit_revision_review_decision.execute(
        project_id=_parse_id(IdentityKind.PROJECT, project_id),
        source_document_revision_id=_parse_id(
            IdentityKind.SOURCE_DOCUMENT_REVISION,
            source_document_revision_id,
        ),
        decision=payload.decision,
        reason=payload.reason,
        actor=actor,
    )
    return RevisionReviewDecisionSchema(
        decision_id=record.decision_id,
        project_id=record.project_id,
        source_document_revision_id=record.source_document_revision_id,
        eligibility_decision=record.eligibility_decision.value,
        reason=record.reason,
        decided_at=record.decided_at,
    )


# --------------------------------------------------------------------------- #
# Corpus snapshots                                                             #
# --------------------------------------------------------------------------- #


@router.get(
    "/projects/{project_id}/corpus-snapshots",
    response_model=PaginatedCorpusSnapshotsSchema,
)
def list_project_corpus_snapshots(
    project_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> dict:
    snapshots = services.list_project_corpus_snapshots.execute(
        _parse_id(IdentityKind.PROJECT, project_id), actor=actor
    )
    items = [snapshot_to_schema(s) for s in snapshots]
    return paginate(items, page=page, page_size=page_size)


@router.post(
    "/corpus-snapshots",
    status_code=status.HTTP_201_CREATED,
    response_model=CorpusSnapshotSchema,
)
def create_corpus_snapshot(
    payload: CreateCorpusSnapshotRequestSchema,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> CorpusSnapshotSchema:
    # Contrato externo canónico: el cliente envía el ``project_id`` completo
    # (``proj_...``). Se valida como ``PlatformId`` (422 fail-closed) y se pasa el
    # cuerpo/slug al caso de uso, que reañade el prefijo. Evita el doble prefijo
    # (``proj_proj_...``) que un body con slug crudo produciría.
    project_pid = _parse_id(IdentityKind.PROJECT, payload.project_id)
    snapshot = services.create_corpus_snapshot.execute(
        project_id=platform_id_body(project_pid),
        document_revision_ids=payload.document_revision_ids,
        actor=actor,
        eligibility_decisions=_eligibility_decisions(payload.eligibility_decisions),
    )
    return snapshot_to_schema(snapshot)


# --------------------------------------------------------------------------- #
# Releases                                                                     #
# --------------------------------------------------------------------------- #


@router.post(
    "/releases",
    status_code=status.HTTP_201_CREATED,
    response_model=ReleaseSchema,
)
def create_release_draft(
    payload: CreateReleaseDraftRequestSchema,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> ReleaseSchema:
    release = services.create_release_draft.execute(
        rag_variant_id=_parse_id(IdentityKind.RAG_VARIANT, payload.rag_variant_id),
        corpus_snapshot_id=_parse_id(
            IdentityKind.CORPUS_SNAPSHOT, payload.corpus_snapshot_id
        ),
        target_binding_key=payload.target_binding_key,
        actor=actor,
    )
    return release_to_schema(release)


@router.get(
    "/projects/{project_id}/releases",
    response_model=PaginatedReleasesSchema,
)
def list_project_releases(
    project_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> dict:
    releases = services.list_project_releases.execute(
        _parse_id(IdentityKind.PROJECT, project_id), actor=actor
    )
    items = [release_to_schema(r) for r in releases]
    return paginate(items, page=page, page_size=page_size)


@router.get("/releases/{rag_release_id}", response_model=ReleaseSchema)
def get_release(
    rag_release_id: str,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> ReleaseSchema:
    release = services.get_release.execute(
        _parse_id(IdentityKind.RAG_RELEASE, rag_release_id), actor=actor
    )
    return release_to_schema(release)


def _run_idempotent(
    *,
    store: IdempotencyStore,
    idempotency_key: str,
    action: str,
    release_id: PlatformId,
    actor: PlatformActor,
    operation,
    request_fields: dict[str, str] | None = None,
) -> dict:
    """Ejecuta un comando de release una sola vez por clave/fingerprint.

    Centraliza la guarda de idempotencia de los cuatro comandos (build/validate/
    publish/retire) para no duplicar el cableado. El fingerprint es ``actor +
    action + rag_release_id`` más ``request_fields`` administrativos que cambian la
    semántica (p. ej. ``reason`` en ``retire``); nunca contenido sensible. Un
    replay de un intento previo **fallido** no devuelve un 200 vacío enmascarando
    el error; se surface con un código estable pidiendo una clave nueva.

    Ownership transaccional: el **caso de uso** posee su propia transacción de
    negocio (``publish`` una corta; ``validate``/``retire`` una corta; ``build``
    una por revisión, incremental). El store de idempotencia usa una **conexión
    dedicada** e independiente, así que sus commits de reserva/terminal jamás
    capturan trabajo de negocio parcial. El router ya **no** envuelve la operación
    en una transacción común (se eliminó el UoW artificial).
    """

    result = IdempotencyGuard(store=store).run(
        idempotency_key=idempotency_key,
        action=action,
        resource_id=release_id.value,
        actor_id=actor.actor_id,
        response_status=status.HTTP_200_OK,
        operation=operation,
        request_fields=request_fields,
    )
    if result.replayed and result.response_status >= 400:
        raise http_error(
            status_code=result.response_status,
            code="IDEMPOTENT_OPERATION_FAILED",
            message=(
                f"a previous {action} attempt for this Idempotency-Key failed; "
                "retry with a new Idempotency-Key"
            ),
        )
    return result.result_json


@router.post(
    "/releases/{rag_release_id}/build",
    response_model=ReleaseBuildAcceptedSchema,
    dependencies=[Depends(_rate_limit_release_build)],
)
def build_release(
    rag_release_id: str,
    idempotency_key: IdempotencyKey,
    payload: ReleaseBuildRequestSchema | None = None,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
    store: IdempotencyStore = Depends(get_idempotency_store),
) -> dict:
    # Build ASÍNCRONO (Fase 8 §D-3b): encola un job durable y responde de inmediato,
    # sin correr el motor en el hilo del request (antes colgaba el socket). El worker
    # corre fuera con su propia conexión; la GUI observa el estado por polling. El
    # guard de idempotencia asegura que un replay devuelve el MISMO job sin re-encolar.
    release_id = _parse_id(IdentityKind.RAG_RELEASE, rag_release_id)
    # `None` = respeta el runtime global; `local`/`remote` lo elige esta corrida.
    embedding_runtime = payload.embedding_runtime if payload is not None else None

    def _operation() -> dict:
        build_job_id = f"bjob_{uuid.uuid4().hex}"
        services.enqueue_release_build.execute(
            rag_release_id=release_id,
            build_job_id=build_job_id,
            actor=actor,
            now=datetime.now(timezone.utc),
        )
        services.submit_release_build(
            build_job_id, release_id, actor, embedding_runtime
        )
        return {
            "build_job_id": build_job_id,
            "rag_release_id": rag_release_id,
            "state": "queued",
        }

    # Un runtime distinto es una intención de build distinta: entra al fingerprint de
    # idempotencia. Omitirlo (None) preserva el fingerprint histórico del build simple.
    request_fields = (
        {"embedding_runtime": embedding_runtime}
        if embedding_runtime is not None
        else None
    )
    return _run_idempotent(
        store=store,
        idempotency_key=idempotency_key,
        action="build",
        release_id=release_id,
        actor=actor,
        operation=_operation,
        request_fields=request_fields,
    )


@router.get(
    "/releases/{rag_release_id}/build-status",
    response_model=ReleaseBuildStatusSchema | None,
)
def get_release_build_status(
    rag_release_id: str,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> dict | None:
    # Read-model del build asíncrono para el polling de la GUI; scope-aware.
    # ``null`` = la release aún no tiene ningún intento de build.
    job = services.get_release_build_status.execute(
        rag_release_id=_parse_id(IdentityKind.RAG_RELEASE, rag_release_id), actor=actor
    )
    return None if job is None else build_job_to_status_schema(job).model_dump(mode="json")


@router.post("/releases/{rag_release_id}/activate")
def activate_release(
    rag_release_id: str,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> dict:
    # Activación EXPLÍCITA (paso separado de publish, ver publication_service): pone
    # los vectores de la release en vivo (is_active=true) y crea el retrieval profile
    # release-scoped que el chatbot consulta. Idempotente. Los errores de dominio
    # (RagReleaseNotActivatable / IncompatibleTargetBinding / PlatformAccessDenied) los
    # traduce el handler global al envelope HTTP.
    # G2: con ``release_serving_only`` activo, esta ruta ya no forma parte del
    # ciclo de vida público — responde 410 ``RELEASE_ACTIVATE_NOT_PUBLIC`` (ver
    # ``NoOpActivateReleaseUseCase``); el chatbot sirve de PUBLISHED + memberships.
    return services.activate_release(
        _parse_id(IdentityKind.RAG_RELEASE, rag_release_id), actor
    )


@router.post(
    "/releases/{rag_release_id}/validate",
    response_model=ReleaseSchema,
)
def validate_release(
    rag_release_id: str,
    idempotency_key: IdempotencyKey,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
    store: IdempotencyStore = Depends(get_idempotency_store),
) -> dict:
    release_id = _parse_id(IdentityKind.RAG_RELEASE, rag_release_id)

    def _operation() -> dict:
        release = services.validate_release.execute(
            rag_release_id=release_id, actor=actor
        )
        return release_to_schema(release).model_dump(mode="json")

    return _run_idempotent(
        store=store,
        idempotency_key=idempotency_key,
        action="validate",
        release_id=release_id,
        actor=actor,
        operation=_operation,
    )


@router.post(
    "/releases/{rag_release_id}/publish",
    response_model=ReleaseSchema,
)
def publish_release(
    rag_release_id: str,
    idempotency_key: IdempotencyKey,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
    store: IdempotencyStore = Depends(get_idempotency_store),
) -> dict:
    release_id = _parse_id(IdentityKind.RAG_RELEASE, rag_release_id)

    def _operation() -> dict:
        release = services.publish_release.execute(
            rag_release_id=release_id, actor=actor
        )
        return release_to_schema(release).model_dump(mode="json")

    return _run_idempotent(
        store=store,
        idempotency_key=idempotency_key,
        action="publish",
        release_id=release_id,
        actor=actor,
        operation=_operation,
    )


@router.post(
    "/releases/{rag_release_id}/retire",
    response_model=ReleaseSchema,
)
def retire_release(
    rag_release_id: str,
    payload: RetireReleaseRequestSchema,
    idempotency_key: IdempotencyKey,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
    store: IdempotencyStore = Depends(get_idempotency_store),
) -> dict:
    release_id = _parse_id(IdentityKind.RAG_RELEASE, rag_release_id)

    def _operation() -> dict:
        release = services.retire_release.execute(
            rag_release_id=release_id, actor=actor, reason=payload.reason
        )
        return release_to_schema(release).model_dump(mode="json")

    return _run_idempotent(
        store=store,
        idempotency_key=idempotency_key,
        action="retire",
        release_id=release_id,
        actor=actor,
        operation=_operation,
        # ``reason`` es material para retire: misma clave con reason distinto es
        # otra petición lógica (fail-closed, no replay).
        request_fields={"reason": payload.reason},
    )
