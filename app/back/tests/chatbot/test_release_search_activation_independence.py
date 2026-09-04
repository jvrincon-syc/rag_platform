"""PR-2 2.1: lock-in that release-scoped chatbot search never depends on ``is_active``.

Release-scoped retrieval (``InMemoryReleaseScopedRetrievalPort`` /
``PostgresReleaseScopedRetrievalPort``) reads vector rows by
project/embedding-profile/indexing-target/corpus-version + release membership
only -- it never reads ``_StoredVector.is_active`` (that flag exists purely for
the legacy, non-release retrieval lane and is only ever flipped ``True`` by the
legacy ``POST /api/indexing/activations`` endpoint). Two parallel serving models
coexist today (audit §3, PR-2 objective); this test locks the invariant the
``SST_FEATURE_RELEASE_SERVING_ONLY`` flag (PR-2 2.1) formalizes: a published
release answers from its indexed-but-never-activated vectors.

Self-contained fixture (not shared with ``test_chatbot_api.py``, which is PR-1
1.1-1.6 committed work this session must not modify) — deliberately never calls
the legacy activation endpoint.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies import build_pipeline_services
from chatbot.domain.models import ChatbotWebhookDeliveryResult, ChatbotWebhookPayload
from core.feature_flags import FeatureFlags
from core.http_auth import AUTH_CREDENTIALS_JSON_KEY, ConfiguredBearerAuth
from rag_platform.domain.identity import IdentityKind, PlatformId
from rag_platform.domain.lifecycle import RagRelease, ReleaseState

from pipeline_fixtures import build_profile, build_target, write_chunk_bundle

AUTH_TOKEN = "token-op-1"
PROJECT_ID = "proj_test"
RAG_VARIANT_ID = "ragv_test"
RAG_RELEASE_ID = "ragr_test"


class _FakeGetReleaseUseCase:
    def __init__(self, release: RagRelease) -> None:
        self._release = release

    def execute(self, release_id: PlatformId, *, actor) -> RagRelease:  # noqa: ANN001
        return self._release


class FakeRagPlatformServices:
    def __init__(self, release: RagRelease) -> None:
        self.get_release = _FakeGetReleaseUseCase(release)


class _InspectableWebhookDispatcher:
    def __init__(self) -> None:
        self.payloads: list[ChatbotWebhookPayload] = []

    def deliver(self, payload: ChatbotWebhookPayload) -> ChatbotWebhookDeliveryResult:
        self.payloads.append(payload)
        return ChatbotWebhookDeliveryResult(
            delivery_id="dispatch-1", target_url="https://example.test/webhook", status_code=202
        )


def _authenticator() -> ConfiguredBearerAuth:
    # G3: op-1 drives the low-level embedding/indexing HTTP mutations that
    # seed this fixture's data (build_nodes/vectors via /runs + /activations);
    # those routes now require an admin principal (require_admin_principal).
    return ConfiguredBearerAuth(
        {
            AUTH_CREDENTIALS_JSON_KEY: (
                '[{"principal_id":"op-1","token":"' + AUTH_TOKEN + '","is_admin":true}]'
            )
        }
    )


def _release() -> RagRelease:
    now = datetime.now(UTC)
    return RagRelease(
        rag_release_id=PlatformId.parse(IdentityKind.RAG_RELEASE, RAG_RELEASE_ID),
        project_id=PlatformId.parse(IdentityKind.PROJECT, PROJECT_ID),
        rag_variant_id=PlatformId.parse(IdentityKind.RAG_VARIANT, RAG_VARIANT_ID),
        corpus_snapshot_id=PlatformId.parse(IdentityKind.CORPUS_SNAPSHOT, "corpus_test"),
        target_binding_key="primary",
        configuration_version=1,
        release_number=1,
        state=ReleaseState.PUBLISHED,
        release_manifest_hash="a" * 64,
        created_by="op-1",
        created_at=now,
        validated_at=now,
    )


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    profile = build_profile()
    chunk_bundle = write_chunk_bundle(
        tmp_path / "chunks",
        child_count=1,
        child_texts=["Fire evacuation procedures for the warehouse floor."],
    )
    webhook = _InspectableWebhookDispatcher()
    services = build_pipeline_services(
        chunks_root=tmp_path / "chunks",
        embeddings_root=tmp_path / "embeddings",
        feature_flags=FeatureFlags(
            embedding_v2=True,
            indexing_bundle_first=True,
            retrieval_v1=True,
            rag_platform_v1=True,
            chatbot_webhook_v1=True,
        ),
        allow_mock_engine=True,
        seed_profiles=[profile],
        seed_targets=[build_target()],
        seed_chunk_bundles=[chunk_bundle],
        lexical_profile_id=profile.profile_id,
        http_authenticator=_authenticator(),
        chatbot_webhook_dispatcher=webhook,
    )
    app = create_app(services=services)
    app.state.test_profile = profile
    app.state.test_chunk_bundle = chunk_bundle
    app.state.rag_platform = FakeRagPlatformServices(_release())
    with TestClient(app) as test_client:
        test_client.headers.update({"Authorization": f"Bearer {AUTH_TOKEN}"})
        yield test_client


def _run_embedding(client: TestClient) -> dict:
    response = client.post(
        "/api/embedding/runs",
        json={
            "chunk_bundle_id": client.app.state.test_chunk_bundle.chunk_bundle_id,
            "profile_id": client.app.state.test_profile.profile_id,
        },
        headers={"Idempotency-Key": "embed-1"},
    )
    assert response.status_code == 202, response.text
    run_id = response.json()["embedding_run_id"]
    for _ in range(200):
        run = client.get(f"/api/embedding/runs/{run_id}").json()
        if run["status"] in {"completed", "failed", "blocked"}:
            return run
    raise AssertionError("embedding run never reached a terminal state")


def _run_indexing(client: TestClient, embedding_bundle_id: str) -> dict:
    response = client.post(
        "/api/indexing/runs",
        json={"embedding_bundle_id": embedding_bundle_id},
        headers={"Idempotency-Key": "index-1"},
    )
    assert response.status_code == 202, response.text
    run_id = response.json()["run_id"]
    for _ in range(200):
        run = client.get(f"/api/indexing/runs/{run_id}").json()
        if run["status"] in {"completed", "failed", "blocked"}:
            return run
    raise AssertionError("indexing run never reached a terminal state")


def test_release_search_no_depende_de_is_active(client: TestClient) -> None:
    """Index vectors, never activate them, and confirm release-scoped search still answers.

    Deliberately never calls ``/api/indexing/activations`` — the only production path that flips a
    vector row's ``is_active`` bit (``InMemoryBundleVectorRepository.activate_bundle``). Every
    freshly appended row starts ``is_active=False``
    (``InMemoryBundleVectorRepository.append_bundle_vectors``); if release-scoped search silently
    started filtering on that flag, this would regress to zero evidence / a
    ``CHATBOT_RELEASE_LANE_UNAVAILABLE``.
    """

    embedding_run = _run_embedding(client)
    indexing_run = _run_indexing(client, embedding_run["produced_embedding_bundle_id"])
    stored_run = client.app.state.indexing_runs.get(indexing_run["run_id"])
    client.app.state.indexing_runs.update(
        stored_run.model_copy(
            update={
                "project_id": PROJECT_ID,
                "rag_variant_id": RAG_VARIANT_ID,
                "rag_release_id": RAG_RELEASE_ID,
            }
        )
    )
    assert stored_run.activation_status == "pending"  # never activated

    response = client.post(
        "/api/chatbot/questions",
        json={
            "project_id": PROJECT_ID,
            "rag_variant_id": RAG_VARIANT_ID,
            "rag_release_id": RAG_RELEASE_ID,
            "question": "warehouse floor evacuation",
            "top_k": 1,
        },
    )

    assert response.status_code == 202, response.text
    assert response.json()["chunks_sent"] == 1
    # Still never activated: the search that just answered did not need it.
    assert (
        client.app.state.indexing_runs.get(indexing_run["run_id"]).activation_status
        == "pending"
    )
