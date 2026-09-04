"""PR-6: per-actor rate limit on ``POST /api/chatbot/questions``.

Self-contained fixture with its OWN dedicated bearer token/actor -- reuses no
token from ``test_chatbot_api.py`` (that file's ~10 ``/questions`` calls all
share ``actor_id="op-1"`` and stay well under the default 30/60s limit, but
``_question_throttle`` in ``chatbot.api.router`` is a process-wide singleton
shared across the whole pytest session, so a test that deliberately exhausts a
key must use one no other test could ever share).

Does not need a real, servable release/lane: the throttle dependency runs
before the route body, so a request that would otherwise 409 on an unpublished
release still consumes -- and is rejected by -- the rate-limit budget.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies import build_pipeline_services
from chatbot.api.router import _QUESTION_RATE_LIMIT_MAX_ATTEMPTS
from core.feature_flags import FeatureFlags
from core.http_auth import AUTH_CREDENTIALS_JSON_KEY, ConfiguredBearerAuth
from rag_platform.domain.identity import IdentityKind, PlatformId
from rag_platform.domain.lifecycle import RagRelease, ReleaseState

TOKEN = "token-rate-limit-question-only"
ACTOR_ID = "op-rate-limit-question-only"
PROJECT_ID = "proj_ratelimit"
RAG_VARIANT_ID = "ragv_ratelimit"
RAG_RELEASE_ID = "ragr_ratelimit"


class _FakeGetReleaseUseCase:
    def execute(self, release_id: PlatformId, *, actor) -> RagRelease:  # noqa: ANN001
        now = datetime.now(UTC)
        return RagRelease(
            rag_release_id=release_id,
            project_id=PlatformId.parse(IdentityKind.PROJECT, PROJECT_ID),
            rag_variant_id=PlatformId.parse(IdentityKind.RAG_VARIANT, RAG_VARIANT_ID),
            corpus_snapshot_id=PlatformId.parse(IdentityKind.CORPUS_SNAPSHOT, "corpus_ratelimit"),
            target_binding_key="primary",
            configuration_version=1,
            release_number=1,
            state=ReleaseState.PUBLISHED,
            release_manifest_hash="a" * 64,
            created_by="op-1",
            created_at=now,
            validated_at=now,
        )


class _FakeRagPlatformServices:
    def __init__(self) -> None:
        self.get_release = _FakeGetReleaseUseCase()


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
        feature_flags=FeatureFlags(rag_platform_v1=True, chatbot_webhook_v1=True),
        allow_mock_engine=True,
        http_authenticator=_authenticator(),
    )
    app = create_app(services=services)
    app.state.rag_platform = _FakeRagPlatformServices()
    with TestClient(app) as test_client:
        test_client.headers.update({"Authorization": f"Bearer {TOKEN}"})
        yield test_client


def _ask(client: TestClient) -> object:
    return client.post(
        "/api/chatbot/questions",
        json={
            "project_id": PROJECT_ID,
            "rag_variant_id": RAG_VARIANT_ID,
            "rag_release_id": RAG_RELEASE_ID,
            "question": "rate limit probe",
        },
    )


def test_bloquea_tras_exceder_el_limite_de_preguntas_por_actor(client: TestClient) -> None:
    """No indexed lane exists, so every accepted attempt 409s
    (``CHATBOT_RELEASE_LANE_UNAVAILABLE``) -- the point is that the rate
    limiter still counts and eventually rejects it BEFORE that 409 fires."""

    for _ in range(_QUESTION_RATE_LIMIT_MAX_ATTEMPTS):
        response = _ask(client)
        assert response.status_code != 429, response.text

    limited = _ask(client)

    assert limited.status_code == 429, limited.text
    assert limited.json()["error"]["code"] == "CHATBOT_QUESTION_RATE_LIMITED"
    assert "Retry-After" in limited.headers
