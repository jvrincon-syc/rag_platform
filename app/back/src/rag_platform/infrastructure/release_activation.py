"""Activación explícita de una release (poner sus vectores en vivo).

Publicar una release es solo una transición de estado (ver
``publication_service``); NUNCA toca ``is_active`` ni crea retrieval profiles.
Poner los vectores en vivo es un paso SEPARADO y explícito, que aquí se cablea
como acción de operador sobre la release ya construida:

    build  -> INSERT vectores (is_active = false)
    activate (esto) -> activate_bundle(): is_active = true + retrieval profile

Reconstruye el ``indexing_run`` de cada bundle de la release a partir de la
MISMA idempotency-key que usó el build (``index`` + release + bundle + target),
así no hace falta persistir el ``run_id`` en un read-model nuevo. Cada bundle se
activa con el caso de uso existente ``ActivateIndexedBundleUseCase``, con el
consumer scope ``chatbot/release-scoped-dispatch`` (el mismo que el dispatcher
release-scoped del chatbot usa para resolver su lane), de modo que el retrieval
profile que crea la activación es exactamente el que el chatbot espera.
"""

from __future__ import annotations

from embedding.infrastructure.filesystem.artifact_store import (
    FilesystemEmbeddingBundleArtifactStore,
)
from embedding.infrastructure.postgres.repositories import (
    PostgresEmbeddingBundleRepository,
    PostgresEmbeddingProfileRepository,
    PostgresIndexingTargetRepository,
    PostgresReadinessCheckRepository,
)
from indexing.application.bundle_first.activation import (
    ActivateIndexedBundleUseCase,
    ActivationRequest,
)
from indexing.infrastructure.postgres.bundle_first import (
    PostgresIndexingRunRepository,
    PsycopgTransactionManager,
)
from indexing.infrastructure.postgres.vector_repository import PostgresVectorRepository
from rag_platform.application.platform_access import (
    PlatformActor,
    require_project_operator,
)
from rag_platform.domain.errors import IncompatibleTargetBinding, RagReleaseNotActivatable
from rag_platform.domain.identity import PlatformId
from rag_platform.infrastructure.postgres.project_repositories import (
    PostgresTargetBindingResolver,
)
from rag_platform.infrastructure.postgres.release_repositories import (
    PostgresRagReleaseMembershipRepository,
    PostgresRagReleaseRepository,
)
from rag_platform.infrastructure.release_build_resolver import _idempotency_key
from retrieval.infrastructure.postgres.repositories import (
    PostgresRetrievalProfileRepository,
)

# El chatbot resuelve su lane release-scoped con este scope fijo (ver
# ``chatbot/infrastructure/release_scoped_retrieval.py``). Activar con el mismo
# scope garantiza que el retrieval profile creado sea el que el chatbot consulta.
_CONSUMER_SCOPE_TYPE = "chatbot"
_CONSUMER_SCOPE_ID = "release-scoped-dispatch"


def activate_rag_release(
    *,
    connection: object,
    storage_roots: object,
    rag_release_id: PlatformId,
    actor: PlatformActor,
    access_policy: object,
) -> dict[str, object]:
    """Activa (pone en vivo) todos los bundles de una release construida.

    Idempotente: ``activate_bundle`` reactiva el mismo bundle sin duplicar y
    upserta el retrieval profile determinista.

    Raises:
        PlatformAccessDenied: si el actor no es operador del proyecto.
        IncompatibleTargetBinding: si el binding versionado ya no existe.
        RagReleaseNotActivatable: si la release no tiene bundles construidos o
            falta el indexing run de alguno (hay que (re)construir primero).
    """

    releases = PostgresRagReleaseRepository(connection)
    memberships_repo = PostgresRagReleaseMembershipRepository(connection)
    bindings = PostgresTargetBindingResolver(connection)

    release = releases.get(rag_release_id)
    require_project_operator(
        policy=access_policy, actor=actor, project_id=release.project_id
    )

    binding = bindings.find_binding(
        release.project_id, release.configuration_version, release.target_binding_key
    )
    if binding is None:
        raise IncompatibleTargetBinding(
            f"target binding {release.target_binding_key!r} is no longer allowed"
        )
    target_id = binding.indexing_target_id

    # Bundles distintos de la release, en orden de aparición (una release puede
    # tener varios bundles; el profile es el mismo y las filas se acumulan).
    seen: set[str] = set()
    bundle_ids: list[str] = []
    for membership in memberships_repo.list_for_release(rag_release_id):
        if membership.embedding_bundle_id not in seen:
            seen.add(membership.embedding_bundle_id)
            bundle_ids.append(membership.embedding_bundle_id)

    if not bundle_ids:
        raise RagReleaseNotActivatable(
            f"release {rag_release_id.value} has no built bundles; build it first"
        )

    embeddings_root = storage_roots.resolve_root(release.project_id, "embeddings")
    runs = PostgresIndexingRunRepository(connection)
    activate = ActivateIndexedBundleUseCase(
        runs=runs,
        bundles=PostgresEmbeddingBundleRepository(connection),
        profiles=PostgresEmbeddingProfileRepository(connection),
        targets=PostgresIndexingTargetRepository(connection),
        vectors=PostgresVectorRepository(connection),
        artifacts=FilesystemEmbeddingBundleArtifactStore(root=embeddings_root),
        retrieval_profiles=PostgresRetrievalProfileRepository(connection),
        readiness_checks=PostgresReadinessCheckRepository(connection),
        transactions=PsycopgTransactionManager(connection),
    )

    details: list[dict[str, object]] = []
    total_rows = 0
    profile_ids: set[str] = set()
    for bundle_id in bundle_ids:
        run = runs.find_by_idempotency_key(
            _idempotency_key("index", rag_release_id.value, bundle_id, target_id)
        )
        if run is None:
            raise RagReleaseNotActivatable(
                f"no indexing run for bundle {bundle_id} of release "
                f"{rag_release_id.value}; rebuild the release before activating"
            )
        result = activate.execute(
            ActivationRequest(
                run_id=run.run_id,
                consumer_scope_type=_CONSUMER_SCOPE_TYPE,
                consumer_scope_id=_CONSUMER_SCOPE_ID,
            )
        )
        total_rows += result.activated_rows
        profile_ids.add(result.retrieval_profile_id)
        details.append(
            {
                "embedding_bundle_id": bundle_id,
                "indexing_run_id": run.run_id,
                "retrieval_profile_id": result.retrieval_profile_id,
                "activated_rows": result.activated_rows,
            }
        )

    return {
        "rag_release_id": rag_release_id.value,
        "status": "activated",
        "activated_bundles": len(details),
        "activated_rows": total_rows,
        "retrieval_profile_ids": sorted(profile_ids),
        "details": details,
    }
