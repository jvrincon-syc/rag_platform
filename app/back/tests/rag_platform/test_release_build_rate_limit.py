"""PR-6: per-actor rate limit on ``POST /api/platform/releases/{id}/build``.

Self-contained fixture with its OWN dedicated bearer token/actor (never reused
by ``test_platform_api.py`` or any other file) -- ``_build_throttle`` in
``rag_platform.api.router`` is a process-wide, module-level singleton shared
across the whole pytest session, so a test that intentionally exhausts it must
use an actor no other test's request could ever count against.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies import build_pipeline_services
from core.feature_flags import FeatureFlags
from core.http_auth import AUTH_CREDENTIALS_JSON_KEY, ConfiguredBearerAuth
from rag_platform.api.router import _BUILD_RATE_LIMIT_MAX_ATTEMPTS

TOKEN = "token-rate-limit-build-only"
ACTOR_ID = "op-rate-limit-build-only"


def _authenticator() -> ConfiguredBearerAuth:
    return ConfiguredBearerAuth(
        {
            AUTH_CREDENTIALS_JSON_KEY: (
                '[{"principal_id":"' + ACTOR_ID + '","token":"' + TOKEN + '"}]'
            )
        }
    )


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    services = build_pipeline_services(
        chunks_root=tmp_path / "chunks",
        embeddings_root=tmp_path / "embeddings",
        feature_flags=FeatureFlags(rag_platform_v1=True),
        allow_mock_engine=True,
        http_authenticator=_authenticator(),
    )
    with TestClient(create_app(services=services)) as test_client:
        test_client.headers.update({"Authorization": f"Bearer {TOKEN}"})
        yield test_client


def _build(client: TestClient, idempotency_key: str):
    return client.post(
        "/api/platform/releases/ragr_missing/build",
        headers={"Idempotency-Key": idempotency_key},
    )


def test_bloquea_tras_exceder_el_limite_de_builds_por_actor(client: TestClient) -> None:
    """The ``_BUILD_RATE_LIMIT_MAX_ATTEMPTS``-th request from this actor still
    runs (the release lookup 404s first); the next one is rate-limited before
    it ever reaches the route body."""

    for i in range(_BUILD_RATE_LIMIT_MAX_ATTEMPTS):
        response = _build(client, f"k-{i}")
        assert response.status_code == 404, response.text

    limited = _build(client, "k-over-limit")

    assert limited.status_code == 429, limited.text
    assert limited.json()["error"]["code"] == "RELEASE_BUILD_RATE_LIMITED"
    assert "Retry-After" in limited.headers


def test_no_bloquea_a_otro_actor_cuando_el_primero_agoto_su_cupo(
    tmp_path: Path,
) -> None:
    """The throttle is per-actor: a distinct actor's own budget is untouched.

    Uses its own pair of dedicated tokens (not the module-level ``ACTOR_ID`` the
    previous test already exhausts) -- ``_build_throttle`` is a process-wide
    singleton shared across the whole pytest session, so reusing a key another
    test already exhausted would make this test order-dependent.
    """

    exhausted_token = "token-rate-limit-build-exhausted"
    exhausted_actor_id = "op-rate-limit-build-exhausted"
    other_token = "token-rate-limit-build-other"
    other_actor_id = "op-rate-limit-build-other"
    authenticator = ConfiguredBearerAuth(
        {
            AUTH_CREDENTIALS_JSON_KEY: (
                "["
                '{"principal_id":"'
                + exhausted_actor_id
                + '","token":"'
                + exhausted_token
                + '"},'
                '{"principal_id":"' + other_actor_id + '","token":"' + other_token + '"}'
                "]"
            )
        }
    )
    services = build_pipeline_services(
        chunks_root=tmp_path / "chunks",
        embeddings_root=tmp_path / "embeddings",
        feature_flags=FeatureFlags(rag_platform_v1=True),
        allow_mock_engine=True,
        http_authenticator=authenticator,
    )
    with TestClient(create_app(services=services)) as client:
        client.headers.update({"Authorization": f"Bearer {exhausted_token}"})
        for i in range(_BUILD_RATE_LIMIT_MAX_ATTEMPTS):
            assert _build(client, f"k-self-{i}").status_code == 404
        assert _build(client, "k-self-over").status_code == 429

        client.headers.update({"Authorization": f"Bearer {other_token}"})
        response = _build(client, "k-other-1")
        assert response.status_code == 404, response.text
