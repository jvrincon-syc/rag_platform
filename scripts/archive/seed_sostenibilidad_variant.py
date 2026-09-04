"""Seeder de perfil local + variante BGE para proj_sostenibilidad_syc (dev).

El proyecto se creo por UI SIN allowlist de embedding, sin target binding y sin
perfiles de processing/chunking propios, asi que la ingesta se bloquea con
"Ningun perfil de procesamiento usa provider=local". Este script cierra esa cadena
minima, de forma idempotente y en UNA transaccion:

  1. Materializa una version de configuracion con el allowlist ``local-bge-m3-v1`` y
     un binding logico ``primary`` -> target BGE (preserva la config vigente).
  2. Inserta el perfil de procesamiento (provider=local) y el de chunking del
     proyecto (IDs propios; no reusa los de otro proyecto).
  3. Crea la variante RAG que los vincula sobre esa version de configuracion.

Reusa los helpers canonicos de ``seed_project`` (perfiles) para no duplicar SQL.

Uso:
    npm run python -- scripts/rag_platform/seed_sostenibilidad_variant.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "app" / "back" / "src"))
sys.path.insert(0, str(_REPO_ROOT / "scripts" / "indexing"))
sys.path.insert(0, str(_REPO_ROOT / "scripts" / "rag_platform"))

from prepare_postgres_indexing import build_dsn_from_env, load_env_file  # noqa: E402
from seed_project import _resolve_chunking_recipe, _upsert_profile_rows  # noqa: E402

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
_PROJECT_SLUG = "sostenibilidad_syc"
_PROJECT_ID = PlatformId(kind=IdentityKind.PROJECT, value=f"proj_{_PROJECT_SLUG}")
_EMBEDDING_PROFILE_ID = "local-bge-m3-v1"
_TARGET_ID = "target-idx-vec-local-bge-m3-v1"
_BINDING_KEY = "primary"
_VARIANT_SLUG = "local-bge-syc"
# IDs propios del proyecto (los de sst-general ya usan pp_local / cp_structural).
_PROCESSING_SLUG = "local-syc"
_CHUNKING_SLUG = "structural-syc"


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
    chunking_recipe = _resolve_chunking_recipe(strategy="structural", slug=_CHUNKING_SLUG)
    processing_id = f"{IdentityKind.PROCESSING_PROFILE.value}_{_PROCESSING_SLUG}"
    profile_args = SimpleNamespace(
        processing_provider="local",
        processing_engine="pdfium-tesseract",
        processing_revision="2026.08",
    )

    connection = psycopg2.connect(**parse_dsn(dsn))
    summary: dict[str, object] = {
        "project_id": _PROJECT_ID.value,
        "rag_variant_id": f"ragv_{_VARIANT_SLUG}",
        "processing_profile_id": processing_id,
        "chunking_profile_id": chunking_recipe.chunking_id,
    }
    try:
        with connection:
            projects = PostgresProjectRepository(connection)
            current = projects.get(_PROJECT_ID).configuration

            has_profile = any(
                p.embedding_profile_id == _EMBEDDING_PROFILE_ID
                for p in current.embedding_profiles
            )
            has_binding = any(
                b.binding_key == _BINDING_KEY for b in current.target_bindings
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
                            embedding_profile_id=_EMBEDDING_PROFILE_ID, enabled=True
                        ),
                    )
                )
                target_bindings = tuple(current.target_bindings) + (
                    ()
                    if has_binding
                    else (
                        ProjectIndexingTargetBinding(
                            binding_key=_BINDING_KEY,
                            indexing_target_id=_TARGET_ID,
                            embedding_profile_id=_EMBEDDING_PROFILE_ID,
                        ),
                    )
                )
                new_config = CreateProjectConfigurationVersionUseCase(
                    projects=projects, configurations=projects, access_policy=access
                ).execute(
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

            with connection.cursor() as cursor:
                _upsert_profile_rows(
                    cursor,
                    project_id_value=_PROJECT_ID.value,
                    processing_id=processing_id,
                    chunking_recipe=chunking_recipe,
                    args=profile_args,
                )

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
                        chunking_profile_id=chunking_recipe.effective_slug,
                        embedding_profile_id=_EMBEDDING_PROFILE_ID,
                        target_binding_key=_BINDING_KEY,
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
