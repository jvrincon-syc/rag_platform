"""Auto-provisioning del setup RAG por defecto de un proyecto (Fase UI).

Un proyecto recien creado por la UI nace sin allowlist de embedding, sin target
binding y sin perfiles de processing/chunking, asi que la ingesta se bloquea. Esta
funcion cierra esa cadena minima de forma idempotente y en UNA transaccion, igual
que el seeder de dev pero server-side y parametrizado por ``embedding_backend``:

  local | lightning -> perfil BGE (mismo vector space; el runtime local/remoto se
                       elige por-build). voyage -> perfil Voyage (otro vector space).

Reusa los casos de uso existentes (config version + variante); la creacion de los
perfiles de catalogo (processing/chunking) es INSERT directo (no hay caso de uso,
son filas de receta con fingerprint inmutable), como en el seeder.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Literal

from rag_platform.application.platform_access import PlatformActor
from rag_platform.application.project_configuration_service import (
    CreateProjectConfigurationVersionUseCase,
    UpdateProjectConfigurationRequest,
)
from rag_platform.application.recipe_service import (
    CreateRagVariantRequest,
    CreateRagVariantUseCase,
)
from rag_platform.domain.errors import DuplicateVariantRecipe
from rag_platform.domain.identity import IdentityKind, PlatformId
from rag_platform.domain.models import (
    ProjectEmbeddingProfile,
    ProjectIndexingTargetBinding,
    compute_chunking_profile_fingerprint,
)
from rag_platform.infrastructure.in_memory.repositories import AllowAllAccessPolicy
from rag_platform.infrastructure.postgres.project_repositories import (
    PostgresChunkingProfileRepository,
    PostgresProcessingProfileRepository,
    PostgresProjectRepository,
    PostgresRagVariantRepository,
    PostgresTargetBindingResolver,
)

EmbeddingBackend = Literal["local", "lightning", "voyage"]

# Mapa backend -> (perfil de embedding global, target compatible, binding key logico,
# prefijo de slug de variante). local y lightning comparten perfil BGE: difieren solo
# en el runtime de build (EMBEDDING_DOC_EMBED), no en el vector space.
_BACKENDS: dict[str, tuple[str, str, str, str]] = {
    "local": ("local-bge-m3-v1", "target-idx-vec-local-bge-m3-v1", "primary", "bge"),
    "lightning": ("local-bge-m3-v1", "target-idx-vec-local-bge-m3-v1", "primary", "bge"),
    "voyage": (
        "local-voyage-4-v1",
        "target-idx-vec-local-voyage-4-v1",
        "voyage",
        "voyage",
    ),
}

_ACTOR = PlatformActor(actor_id="ui-provisioner")


def _fingerprint(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _dsn() -> str | None:
    return (os.environ.get("RAG_PLATFORM_POSTGRES_DSN") or "").strip() or (
        os.environ.get("SST_POSTGRES_DSN") or ""
    ).strip()


def provision_default_variant(
    *, project_slug: str, embedding_backend: EmbeddingBackend
) -> dict[str, object]:
    """Provisiona (idempotente) allowlist+binding+processing+chunking+variante.

    Raises:
        ValueError: backend desconocido o sin DSN de PostgreSQL.
    """

    if embedding_backend not in _BACKENDS:
        raise ValueError(f"unknown embedding_backend: {embedding_backend!r}")
    embedding_profile_id, target_id, binding_key, variant_prefix = _BACKENDS[
        embedding_backend
    ]

    dsn = _dsn()
    if not dsn:
        raise ValueError("postgres_dsn_missing")

    import psycopg2
    from psycopg2.extensions import parse_dsn

    from embedding.infrastructure.postgres.repositories import (
        PostgresEmbeddingProfileRepository,
    )

    project_id = PlatformId(kind=IdentityKind.PROJECT, value=f"proj_{project_slug}")
    processing_slug = f"local-{project_slug}"
    processing_id = f"{IdentityKind.PROCESSING_PROFILE.value}_{processing_slug}"
    chunking_slug = f"structural-{project_slug}"
    chunking_id = f"{IdentityKind.CHUNKING_PROFILE.value}_{chunking_slug}"
    chunking_fp = compute_chunking_profile_fingerprint(
        strategy="structural", sanitized_config={}
    )
    variant_slug = f"{variant_prefix}-{project_slug}"
    access = AllowAllAccessPolicy()
    summary: dict[str, object] = {
        "project_id": project_id.value,
        "embedding_backend": embedding_backend,
        "rag_variant_id": f"ragv_{variant_slug}",
    }

    connection = psycopg2.connect(**parse_dsn(dsn))
    try:
        with connection:
            projects = PostgresProjectRepository(connection)
            current = projects.get(project_id).configuration

            has_profile = any(
                p.embedding_profile_id == embedding_profile_id
                for p in current.embedding_profiles
            )
            has_binding = any(b.binding_key == binding_key for b in current.target_bindings)
            if has_profile and has_binding:
                config_version = current.version
            else:
                embedding_profiles = tuple(current.embedding_profiles) + (
                    ()
                    if has_profile
                    else (
                        ProjectEmbeddingProfile(
                            embedding_profile_id=embedding_profile_id, enabled=True
                        ),
                    )
                )
                target_bindings = tuple(current.target_bindings) + (
                    ()
                    if has_binding
                    else (
                        ProjectIndexingTargetBinding(
                            binding_key=binding_key,
                            indexing_target_id=target_id,
                            embedding_profile_id=embedding_profile_id,
                        ),
                    )
                )
                new_config = CreateProjectConfigurationVersionUseCase(
                    projects=projects, configurations=projects, access_policy=access
                ).execute(
                    project_id,
                    request=UpdateProjectConfigurationRequest(
                        corpus_organization_policy=current.corpus_organization_policy,
                        document_types=current.document_types,
                        embedding_profiles=embedding_profiles,
                        target_bindings=target_bindings,
                    ),
                    actor=_ACTOR,
                )
                config_version = new_config.version
            summary["configuration_version"] = config_version

            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO document_processing_profiles (processing_profile_id,"
                    " project_id, provider, engine, observed_revision, origin,"
                    " sanitized_config_json, fingerprint, status)"
                    " VALUES (%s, %s, 'local', 'pdfium-tesseract', '2026.08', 'local',"
                    " '{}'::jsonb, %s, 'verified')"
                    " ON CONFLICT (processing_profile_id) DO NOTHING",
                    (
                        processing_id,
                        project_id.value,
                        _fingerprint("processing", "local", "pdfium-tesseract", "2026.08"),
                    ),
                )
                cursor.execute(
                    "INSERT INTO chunking_profiles (chunking_profile_id, project_id,"
                    " strategy, sanitized_config_json, fingerprint, status)"
                    " VALUES (%s, %s, 'structural', '{}'::jsonb, %s, 'verified')"
                    " ON CONFLICT (chunking_profile_id) DO NOTHING",
                    (chunking_id, project_id.value, chunking_fp),
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
                        variant_slug=variant_slug,
                        project_id=project_slug,
                        processing_profile_id=processing_slug,
                        chunking_profile_id=chunking_slug,
                        embedding_profile_id=embedding_profile_id,
                        target_binding_key=binding_key,
                        configuration_version=config_version,
                    ),
                    actor_id="ui-provisioner",
                )
                summary["variant"] = "created"
                summary["semantic_recipe_fingerprint"] = (
                    variant.semantic_recipe_fingerprint
                )
            except DuplicateVariantRecipe:
                summary["variant"] = "exists"
    finally:
        connection.close()

    summary["status"] = "provisioned"
    return summary


# Claves semánticas de una receta de chunking con hiperparámetros libres. El runtime
# (``runtime_chunking_profiles._build_custom``) lee exactamente estas claves; las
# ausentes caen a los defaults de v1. ``include_section_context`` es opcional.
_CHUNKING_PARAM_KEYS = (
    "child_min_tokens",
    "child_target_tokens",
    "child_max_tokens",
    "overlap_min_tokens",
    "overlap_max_tokens",
)


def provision_custom_chunking_variant(
    *,
    project_slug: str,
    embedding_backend: EmbeddingBackend,
    chunking_params: dict[str, object],
) -> dict[str, object]:
    """Crea (idempotente) una variante con una receta de chunking a medida.

    A diferencia de ``provision_default_variant`` (preset v1), persiste un chunking
    profile ``structural-custom`` con los hiperparámetros dados y una variante que lo
    referencia. Valida los invariantes ANTES de persistir construyendo el
    ``RuntimeChunkingProfile`` (mismo motor que corre el build), así una receta
    incoherente (p. ej. max < target, overlap fuera de rango) se rechaza sin dejar
    filas basura.

    Raises:
        ValueError: backend desconocido, sin DSN, o params de chunking inválidos.
    """

    if embedding_backend not in _BACKENDS:
        raise ValueError(f"unknown embedding_backend: {embedding_backend!r}")
    embedding_profile_id, target_id, binding_key, variant_prefix = _BACKENDS[
        embedding_backend
    ]

    dsn = _dsn()
    if not dsn:
        raise ValueError("postgres_dsn_missing")

    # Config semántica: solo claves numéricas presentes + include_section_context.
    config: dict[str, object] = {}
    for key in _CHUNKING_PARAM_KEYS:
        if key in chunking_params and chunking_params[key] is not None:
            config[key] = int(chunking_params[key])  # type: ignore[arg-type]
    if "overlap_ratio" in chunking_params and chunking_params["overlap_ratio"] is not None:
        config["overlap_ratio"] = float(chunking_params["overlap_ratio"])  # type: ignore[arg-type]
    if chunking_params.get("include_section_context"):
        config["include_section_context"] = True

    # Validación fail-closed con el MISMO motor del build (invariantes de tokens/overlap).
    from chunking.domain.errors import ChunkingProfileError
    from chunking.domain.models import ChunkingProfile as RuntimeChunkingProfile

    _CUSTOM_DEFAULTS = {
        "child_min_tokens": 250,
        "child_target_tokens": 350,
        "child_max_tokens": 450,
        "overlap_ratio": 0.12,
        "overlap_min_tokens": 30,
        "overlap_max_tokens": 60,
    }
    try:
        RuntimeChunkingProfile(
            profile_id="validate",
            child_min_tokens=int(config.get("child_min_tokens", _CUSTOM_DEFAULTS["child_min_tokens"])),
            child_target_tokens=int(
                config.get("child_target_tokens", _CUSTOM_DEFAULTS["child_target_tokens"])
            ),
            child_max_tokens=int(config.get("child_max_tokens", _CUSTOM_DEFAULTS["child_max_tokens"])),
            overlap_ratio=float(config.get("overlap_ratio", _CUSTOM_DEFAULTS["overlap_ratio"])),
            overlap_min_tokens=int(
                config.get("overlap_min_tokens", _CUSTOM_DEFAULTS["overlap_min_tokens"])
            ),
            overlap_max_tokens=int(
                config.get("overlap_max_tokens", _CUSTOM_DEFAULTS["overlap_max_tokens"])
            ),
            include_section_context=bool(config.get("include_section_context", False)),
        )
    except (ChunkingProfileError, ValueError, TypeError) as error:
        raise ValueError(f"invalid chunking params: {error}") from error

    import psycopg2
    from psycopg2.extensions import parse_dsn

    from embedding.infrastructure.postgres.repositories import (
        PostgresEmbeddingProfileRepository,
    )

    project_id = PlatformId(kind=IdentityKind.PROJECT, value=f"proj_{project_slug}")
    processing_slug = f"local-{project_slug}"
    processing_id = f"{IdentityKind.PROCESSING_PROFILE.value}_{processing_slug}"
    # Slug del chunking derivado de los params (misma receta -> mismo slug -> reuso).
    param_fp = _fingerprint("structural-custom", json.dumps(config, sort_keys=True))
    chunking_slug = f"custom-{param_fp[:12]}-{project_slug}"
    chunking_id = f"{IdentityKind.CHUNKING_PROFILE.value}_{chunking_slug}"
    chunking_fp = compute_chunking_profile_fingerprint(
        strategy="structural-custom", sanitized_config=config
    )
    variant_slug = f"{variant_prefix}-{chunking_slug}"
    access = AllowAllAccessPolicy()
    summary: dict[str, object] = {
        "project_id": project_id.value,
        "embedding_backend": embedding_backend,
        "chunking_profile_id": chunking_id,
        "chunking_config": config,
        "rag_variant_id": f"ragv_{variant_slug}",
    }

    connection = psycopg2.connect(**parse_dsn(dsn))
    try:
        with connection:
            projects = PostgresProjectRepository(connection)
            current = projects.get(project_id).configuration

            has_profile = any(
                p.embedding_profile_id == embedding_profile_id
                for p in current.embedding_profiles
            )
            has_binding = any(b.binding_key == binding_key for b in current.target_bindings)
            if has_profile and has_binding:
                config_version = current.version
            else:
                embedding_profiles = tuple(current.embedding_profiles) + (
                    ()
                    if has_profile
                    else (
                        ProjectEmbeddingProfile(
                            embedding_profile_id=embedding_profile_id, enabled=True
                        ),
                    )
                )
                target_bindings = tuple(current.target_bindings) + (
                    ()
                    if has_binding
                    else (
                        ProjectIndexingTargetBinding(
                            binding_key=binding_key,
                            indexing_target_id=target_id,
                            embedding_profile_id=embedding_profile_id,
                        ),
                    )
                )
                new_config = CreateProjectConfigurationVersionUseCase(
                    projects=projects, configurations=projects, access_policy=access
                ).execute(
                    project_id,
                    request=UpdateProjectConfigurationRequest(
                        corpus_organization_policy=current.corpus_organization_policy,
                        document_types=current.document_types,
                        embedding_profiles=embedding_profiles,
                        target_bindings=target_bindings,
                    ),
                    actor=_ACTOR,
                )
                config_version = new_config.version
            summary["configuration_version"] = config_version

            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO document_processing_profiles (processing_profile_id,"
                    " project_id, provider, engine, observed_revision, origin,"
                    " sanitized_config_json, fingerprint, status)"
                    " VALUES (%s, %s, 'local', 'pdfium-tesseract', '2026.08', 'local',"
                    " '{}'::jsonb, %s, 'verified')"
                    " ON CONFLICT (processing_profile_id) DO NOTHING",
                    (
                        processing_id,
                        project_id.value,
                        _fingerprint("processing", "local", "pdfium-tesseract", "2026.08"),
                    ),
                )
                cursor.execute(
                    "INSERT INTO chunking_profiles (chunking_profile_id, project_id,"
                    " strategy, sanitized_config_json, fingerprint, status)"
                    " VALUES (%s, %s, 'structural-custom', %s::jsonb, %s, 'verified')"
                    " ON CONFLICT (chunking_profile_id) DO NOTHING",
                    (
                        chunking_id,
                        project_id.value,
                        json.dumps(config),
                        chunking_fp,
                    ),
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
                        variant_slug=variant_slug,
                        project_id=project_slug,
                        processing_profile_id=processing_slug,
                        chunking_profile_id=chunking_slug,
                        embedding_profile_id=embedding_profile_id,
                        target_binding_key=binding_key,
                        configuration_version=config_version,
                    ),
                    actor_id="ui-provisioner",
                )
                summary["variant"] = "created"
                summary["semantic_recipe_fingerprint"] = (
                    variant.semantic_recipe_fingerprint
                )
            except DuplicateVariantRecipe:
                summary["variant"] = "exists"
    finally:
        connection.close()

    summary["status"] = "provisioned"
    return summary
