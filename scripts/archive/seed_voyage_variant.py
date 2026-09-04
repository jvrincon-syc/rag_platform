"""Seeder de la variante Voyage para proj_sst-general (dev, idempotente).

La variante BGE ya existe con el binding logico ``primary`` atado a su perfil de
embedding. Voyage usa OTRO vector space (perfil ``local-voyage-4-v1`` -> tabla
``idx_vec_local_voyage_4_v1``), asi que necesita su propio binding en la allowlist:
un ``binding_key`` ``voyage`` compatible con el perfil voyage.

Pasos (una sola transaccion atomica):
  1. Materializa una version nueva de configuracion del proyecto que preserva la
     vigente y ANADE: el perfil voyage al allowlist y un binding ``voyage``.
  2. Crea la variante ``ragv_local-voyage`` sobre esa version, reusando el
     processing/chunking del proyecto (solo cambia el embedding).

Reusa el perfil de embedding GLOBAL voyage ya seedeado por migraciones; no crea
tablas ni motores. Re-ejecutable: reporta ``exists`` en vez de duplicar.

Uso:
    npm run python -- scripts/rag_platform/seed_voyage_variant.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "app" / "back" / "src"))
sys.path.insert(0, str(_REPO_ROOT / "scripts" / "indexing"))

from prepare_postgres_indexing import build_dsn_from_env, load_env_file  # noqa: E402

from rag_platform.application.platform_access import PlatformActor  # noqa: E402
from rag_platform.application.project_configuration_service import (  # noqa: E402
    CreateProjectConfigurationVersionUseCase,
    UpdateProjectConfigurationRequest,
)
from rag_platform.application.recipe_service import (  # noqa: E402
    CreateRagVariantRequest,
    CreateRagVariantUseCase,
)
from rag_platform.domain.errors import DuplicateVariantRecipe  # noqa: E402
from rag_platform.domain.identity import IdentityKind, PlatformId  # noqa: E402
from rag_platform.domain.models import (  # noqa: E402
    ProjectEmbeddingProfile,
    ProjectIndexingTargetBinding,
)
from rag_platform.infrastructure.in_memory.repositories import (  # noqa: E402
    AllowAllAccessPolicy,
)
from rag_platform.infrastructure.postgres.project_repositories import (  # noqa: E402
    PostgresChunkingProfileRepository,
    PostgresProcessingProfileRepository,
    PostgresProjectRepository,
    PostgresRagVariantRepository,
    PostgresTargetBindingResolver,
)

_ACTOR = PlatformActor(actor_id="seed-operator")
_PROJECT_SLUG = "sst-general"
_PROJECT_ID = PlatformId(kind=IdentityKind.PROJECT, value=f"proj_{_PROJECT_SLUG}")
_VOYAGE_PROFILE_ID = "local-voyage-4-v1"
_VOYAGE_TARGET_ID = "target-idx-vec-local-voyage-4-v1"
_VOYAGE_BINDING_KEY = "voyage"
_VARIANT_SLUG = "local-voyage"
# Processing/chunking del proyecto (creados por el seed BGE): solo cambia embedding.
_PROCESSING_SLUG = "local"
_CHUNKING_SLUG = "structural"


def main() -> int:
    dsn = build_dsn_from_env(dict(load_env_file(_REPO_ROOT / "secrets.env")))
    if not dsn:
        print(json.dumps({"status": "blocked", "reason": "postgres_dsn_missing"}))
        return 2

    import psycopg2
    from psycopg2.extensions import parse_dsn

    from embedding.infrastructure.postgres.repositories import (
        PostgresEmbeddingProfileRepository,
    )

    access = AllowAllAccessPolicy()
    connection = psycopg2.connect(**parse_dsn(dsn))
    summary: dict[str, object] = {
        "project_id": _PROJECT_ID.value,
        "embedding_profile_id": _VOYAGE_PROFILE_ID,
        "binding_key": _VOYAGE_BINDING_KEY,
        "rag_variant_id": f"ragv_{_VARIANT_SLUG}",
    }
    try:
        with connection:
            projects = PostgresProjectRepository(connection)
            current = projects.get(_PROJECT_ID).configuration

            has_profile = any(
                p.embedding_profile_id == _VOYAGE_PROFILE_ID
                for p in current.embedding_profiles
            )
            has_binding = any(
                b.binding_key == _VOYAGE_BINDING_KEY for b in current.target_bindings
            )

            if has_profile and has_binding:
                summary["configuration"] = "exists"
                config_version = current.version
            else:
                embedding_profiles = tuple(current.embedding_profiles) + (
                    ()
                    if has_profile
                    else (
                        ProjectEmbeddingProfile(
                            embedding_profile_id=_VOYAGE_PROFILE_ID, enabled=True
                        ),
                    )
                )
                target_bindings = tuple(current.target_bindings) + (
                    ()
                    if has_binding
                    else (
                        ProjectIndexingTargetBinding(
                            binding_key=_VOYAGE_BINDING_KEY,
                            indexing_target_id=_VOYAGE_TARGET_ID,
                            embedding_profile_id=_VOYAGE_PROFILE_ID,
                        ),
                    )
                )
                use_case = CreateProjectConfigurationVersionUseCase(
                    projects=projects, configurations=projects, access_policy=access
                )
                new_config = use_case.execute(
                    _PROJECT_ID,
                    request=UpdateProjectConfigurationRequest(
                        corpus_organization_policy=current.corpus_organization_policy,
                        document_types=current.document_types,
                        embedding_profiles=embedding_profiles,
                        target_bindings=target_bindings,
                    ),
                    actor=_ACTOR,
                )
                summary["configuration"] = "created"
                config_version = new_config.version
            summary["configuration_version"] = config_version

            variant_use_case = CreateRagVariantUseCase(
                variants=PostgresRagVariantRepository(connection),
                processing_profiles=PostgresProcessingProfileRepository(connection),
                chunking_profiles=PostgresChunkingProfileRepository(connection),
                embedding_profiles=PostgresEmbeddingProfileRepository(connection),
                target_bindings=PostgresTargetBindingResolver(connection),
                access_policy=access,
            )
            try:
                variant = variant_use_case.execute(
                    CreateRagVariantRequest(
                        variant_slug=_VARIANT_SLUG,
                        project_id=_PROJECT_SLUG,
                        processing_profile_id=_PROCESSING_SLUG,
                        chunking_profile_id=_CHUNKING_SLUG,
                        embedding_profile_id=_VOYAGE_PROFILE_ID,
                        target_binding_key=_VOYAGE_BINDING_KEY,
                        configuration_version=config_version,
                    ),
                    actor_id="seed-operator",
                )
                summary["variant"] = "created"
                summary["semantic_recipe_fingerprint"] = (
                    variant.semantic_recipe_fingerprint
                )
            except DuplicateVariantRecipe:
                summary["variant"] = "exists"
    finally:
        connection.close()

    summary["status"] = "seeded"
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
