from __future__ import annotations

import pytest

from embedding.application.engine_registry import (
    DefaultEmbeddingEngineRegistry,
    operational_settings,
)
from embedding.domain.errors import (
    EmbeddingEngineNotFound,
    EmbeddingEngineUnavailable,
)
from indexing.infrastructure.embeddings.bge import BgeModelCache
from retrieval.infrastructure.remote_bge import RemoteBgeQueryEngine

from pipeline_fixtures import build_profile


def test_resuelve_el_motor_del_perfil_exacto_cuando_el_provider_existe() -> None:
    registry = DefaultEmbeddingEngineRegistry(environ={}, allow_mock=True)
    profile = build_profile()

    engine = registry.resolve_document_engine(profile)

    assert engine.provider_name == "mock"
    assert engine.model_name == "deterministic"
    assert engine.dimension == profile.dimension


def test_bloquea_cohere_cuando_sigue_siendo_un_stub() -> None:
    registry = DefaultEmbeddingEngineRegistry(environ={}, allow_mock=True)
    profile = build_profile(provider="cohere", model="embed-v4")

    with pytest.raises(EmbeddingEngineUnavailable):
        registry.resolve_document_engine(profile)


def test_bloquea_el_mock_cuando_no_es_dry_run_ni_test() -> None:
    registry = DefaultEmbeddingEngineRegistry(environ={}, allow_mock=False)

    with pytest.raises(EmbeddingEngineUnavailable):
        registry.resolve_document_engine(build_profile())


def test_falla_cuando_el_provider_no_esta_registrado() -> None:
    registry = DefaultEmbeddingEngineRegistry(environ={}, allow_mock=True)
    profile = build_profile(provider="openai", model="text-embedding-3")

    with pytest.raises(EmbeddingEngineNotFound):
        registry.resolve_document_engine(profile)


def test_no_hay_fallback_vectorial_cuando_bge_no_esta_disponible() -> None:
    registry = DefaultEmbeddingEngineRegistry(environ={}, allow_mock=True)
    bge_profile = build_profile(
        provider="bge",
        model="BAAI/bge-m3",
        dimension=1024,
        normalization="l2",
        vector_table="idx_vec_local_bge_m3_v1",
    )

    status = registry.get_runtime_status(bge_profile)

    # Resolution succeeds (the model loads lazily) but nothing ever swaps the
    # provider for another one.
    assert status.provider == "bge"
    assert status.runtime_mode == "local"


def test_el_entorno_no_puede_cambiar_la_configuracion_semantica() -> None:
    profile = build_profile()
    hostile_env = {
        "EMBEDDING_PROVIDER": "voyage",
        "EMBEDDING_MODEL": "voyage-4",
        "EMBEDDING_DIMENSION": "2048",
        "EMBEDDING_DISTANCE_METRIC": "l2",
        "EMBEDDING_BATCH_SIZE": "7",
        "EMBEDDING_TIMEOUT_SECONDS": "11",
    }

    settings = operational_settings(profile, hostile_env)

    assert settings.provider == profile.provider
    assert settings.model == profile.model
    assert settings.dimension == profile.dimension
    assert settings.distance_metric == profile.distance_metric
    assert settings.batch_size == 7
    assert settings.timeout_seconds == 11


def test_reporta_incompatibilidad_cuando_la_dimension_del_motor_difiere() -> None:
    registry = DefaultEmbeddingEngineRegistry(environ={}, allow_mock=True)
    profile = build_profile()
    engine = registry.resolve_document_engine(profile)
    other = build_profile(profile_id="other", dimension=16)

    report = registry.validate_engine_compatibility(other, engine)

    assert report.compatible is False
    assert {mismatch.field_name for mismatch in report.mismatches} == {"dimension"}


def test_reporta_incompatibilidad_cuando_la_normalizacion_difiere() -> None:
    registry = DefaultEmbeddingEngineRegistry(environ={}, allow_mock=True)
    profile = build_profile()
    engine = registry.resolve_document_engine(profile)
    other = build_profile(profile_id="other", normalization="l2")

    report = registry.validate_engine_compatibility(other, engine)

    assert report.compatible is False
    assert {mismatch.field_name for mismatch in report.mismatches} == {"normalization"}


def test_runtime_status_marca_bloqueado_cuando_el_perfil_no_esta_verificado() -> None:
    registry = DefaultEmbeddingEngineRegistry(environ={}, allow_mock=True)
    profile = build_profile(
        compatibility_status="compatibility_not_proven",
        document_enabled=False,
        query_enabled=False,
    )

    status = registry.get_runtime_status(profile)

    assert status.engine_available is True
    assert status.supports_documents is False
    assert status.supports_queries is False
    assert status.blocked_reason == "EMBEDDING_PROFILE_COMPATIBILITY_NOT_PROVEN"


def test_runtime_status_deja_libre_el_bge_m3_legacy() -> None:
    registry = DefaultEmbeddingEngineRegistry(environ={}, allow_mock=True)
    profile = build_profile(
        provider="bge",
        model="BAAI/bge-m3",
        dimension=1024,
        normalization="unknown_normalization",
        vector_table="idx_vec_local_bge_m3_v1",
        compatibility_status="compatibility_not_proven",
        document_enabled=False,
        query_enabled=False,
    )

    status = registry.get_runtime_status(profile)

    assert status.engine_available is True
    assert status.supports_documents is True
    assert status.supports_queries is True
    assert status.blocked_reason is None


def test_comparte_el_bge_model_cache_entre_perfiles_distintos_del_mismo_modelo() -> None:
    """Two distinct bge profile_ids each get their own registry cache entry, but
    both providers hold the SAME injected ``BgeModelCache`` -- the collaborator
    that actually dedupes the ~2GB model load when both name ``BAAI/bge-m3``.
    """

    shared_cache = BgeModelCache()
    registry = DefaultEmbeddingEngineRegistry(
        environ={}, allow_mock=True, bge_model_cache=shared_cache
    )
    first_profile = build_profile(
        profile_id="bge-a",
        provider="bge",
        model="BAAI/bge-m3",
        dimension=1024,
        normalization="l2",
        vector_table="idx_vec_local_bge_m3_v1",
    )
    second_profile = build_profile(
        profile_id="bge-b",
        provider="bge",
        model="BAAI/bge-m3",
        dimension=1024,
        normalization="l2",
        vector_table="idx_vec_local_bge_m3_v1",
    )

    first_engine = registry.resolve_document_engine(first_profile)
    second_engine = registry.resolve_document_engine(second_profile)

    assert first_engine is not second_engine
    assert first_engine.provider.model_cache is shared_cache
    assert second_engine.provider.model_cache is shared_cache


def test_resuelve_y_cachea_el_query_engine_remoto_para_bge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RETRIEVAL_QUERY_EMBED", "remote")
    registry = DefaultEmbeddingEngineRegistry(environ={}, allow_mock=True)
    profile = build_profile(
        profile_id="bge-remote",
        provider="bge",
        model="BAAI/bge-m3",
        dimension=1024,
        normalization="l2",
        vector_table="idx_vec_local_bge_m3_v1",
    )

    first_engine = registry.resolve_query_engine(profile)
    second_engine = registry.resolve_query_engine(profile)

    assert isinstance(first_engine, RemoteBgeQueryEngine)
    assert second_engine is first_engine


def test_trata_la_normalizacion_unknown_del_bge_m3_legacy_como_compatible() -> None:
    registry = DefaultEmbeddingEngineRegistry(environ={}, allow_mock=True)
    profile = build_profile(
        provider="bge",
        model="BAAI/bge-m3",
        dimension=1024,
        normalization="unknown_normalization",
        vector_table="idx_vec_local_bge_m3_v1",
        compatibility_status="compatibility_not_proven",
        document_enabled=False,
        query_enabled=False,
    )

    class LegacyBgeEngine:
        provider_name = "bge"
        model_name = "BAAI/bge-m3"
        dimension = 1024
        normalization = "l2"

    report = registry.validate_engine_compatibility(profile, LegacyBgeEngine())

    assert report.compatible is True
    assert report.mismatches == []
