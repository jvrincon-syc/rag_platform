"""HTTP contract for the chatbot question dispatch API."""

from __future__ import annotations

import logging
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
SCOPED_TOKEN = "token-proj-test"
FOREIGN_SCOPED_TOKEN = "token-proj-other"
PROJECT_ID = "proj_test"
RAG_VARIANT_ID = "ragv_test"
RAG_RELEASE_ID = "ragr_test"
DISTINCT_CHILD_TEXTS = [
    "Fire evacuation procedures for the warehouse floor.",
    "Overtime pay policy for weekend shift workers.",
    "Vacation request approval workflow for managers.",
]


class _FakeGetReleaseUseCase:
    def __init__(self, release: RagRelease) -> None:
        self._release = release

    def execute(self, release_id: PlatformId, *, actor) -> RagRelease:  # noqa: ANN001
        assert actor.actor_id
        assert release_id == self._release.rag_release_id
        return self._release


class _FakeListProjectReleasesUseCase:
    def __init__(self, releases: tuple[RagRelease, ...]) -> None:
        self._releases = releases

    def execute(self, project_id: PlatformId, *, actor) -> tuple[RagRelease, ...]:  # noqa: ANN001
        assert actor.actor_id
        return tuple(
            release for release in self._releases if release.project_id == project_id
        )


class FakeRagPlatformServices:
    def __init__(
        self,
        release: RagRelease,
        *,
        releases: tuple[RagRelease, ...] | None = None,
    ) -> None:
        self.get_release = _FakeGetReleaseUseCase(release)
        self.list_project_releases = _FakeListProjectReleasesUseCase(
            releases if releases is not None else (release,)
        )


class InspectableWebhookDispatcher:
    """Capture chatbot webhook payloads during tests."""

    def __init__(self) -> None:
        self.payloads: list[ChatbotWebhookPayload] = []

    def deliver(self, payload: ChatbotWebhookPayload) -> ChatbotWebhookDeliveryResult:
        self.payloads.append(payload)
        return ChatbotWebhookDeliveryResult(
            delivery_id="dispatch-1",
            target_url="https://example.test/webhook",
            status_code=202,
        )


def _authenticator() -> ConfiguredBearerAuth:
    return ConfiguredBearerAuth(
        {
            AUTH_CREDENTIALS_JSON_KEY: (
                '[{"principal_id":"op-1","token":"'
                + AUTH_TOKEN
                + '"},'
                + '{"principal_id":"proj-test","token":"'
                + SCOPED_TOKEN
                + '","project_scope":["proj_test"]},'
                + '{"principal_id":"proj-other","token":"'
                + FOREIGN_SCOPED_TOKEN
                + '","project_scope":["proj_other"]}]'
            )
        }
    )


def _auth_headers(token: str = AUTH_TOKEN) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _run_embedding(client: TestClient) -> dict:
    payload = {
        "chunk_bundle_id": client.app.state.test_chunk_bundle.chunk_bundle_id,
        "profile_id": client.app.state.test_profile.profile_id,
    }
    response = client.post(
        "/api/embedding/runs",
        json=payload,
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


def _activate_retrieval_profile(client: TestClient) -> str:
    embedding_run = _run_embedding(client)
    indexing_run = _run_indexing(client, embedding_run["produced_embedding_bundle_id"])
    activation = client.post(
        "/api/indexing/activations",
        json={"run_id": indexing_run["run_id"]},
    )
    assert activation.status_code == 200, activation.text
    stored_run = client.app.state.indexing_runs.get(indexing_run["run_id"])
    client.app.state.indexing_runs.update(
        stored_run.model_copy(
            update={
                "project_id": PROJECT_ID,
                "rag_variant_id": RAG_VARIANT_ID,
                "rag_release_id": RAG_RELEASE_ID,
                "activation_status": "active",
            }
        )
    )
    return activation.json()["retrieval_profile_id"]


def _tag_release_context_without_legacy_activation(client: TestClient) -> dict:
    """Simulate a published release whose platform artifacts exist but were never
    activated through the legacy retrieval lane.

    This is the real production shape for release-scoped chatbot dispatch:
    platform builds can leave indexing runs ``completed`` + ``pending`` while the
    release itself is already the authority for what should be queried.
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
    return indexing_run


def _release(
    *,
    rag_release_id: str = RAG_RELEASE_ID,
    project_id: str = PROJECT_ID,
    rag_variant_id: str = RAG_VARIANT_ID,
    release_number: int = 1,
    state: ReleaseState = ReleaseState.PUBLISHED,
) -> RagRelease:
    return RagRelease(
        rag_release_id=PlatformId.parse(IdentityKind.RAG_RELEASE, rag_release_id),
        project_id=PlatformId.parse(IdentityKind.PROJECT, project_id),
        rag_variant_id=PlatformId.parse(IdentityKind.RAG_VARIANT, rag_variant_id),
        corpus_snapshot_id=PlatformId.parse(IdentityKind.CORPUS_SNAPSHOT, "corpus_test"),
        target_binding_key="primary",
        configuration_version=1,
        release_number=release_number,
        state=state,
        release_manifest_hash="a" * 64,
        created_by="op-1",
        created_at=profile_created_at(),
        validated_at=profile_created_at() if state != ReleaseState.DRAFT else None,
        reason="retired for testing" if state == ReleaseState.RETIRED else None,
    )


def profile_created_at():
    from datetime import UTC, datetime

    return datetime.now(UTC)


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    profile = build_profile()
    chunk_bundle = write_chunk_bundle(
        tmp_path / "chunks",
        child_texts=DISTINCT_CHILD_TEXTS,
    )
    webhook = InspectableWebhookDispatcher()
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
    app.state.test_webhook = webhook
    app.state.rag_platform = FakeRagPlatformServices(_release())
    with TestClient(app) as test_client:
        test_client.headers.update(_auth_headers())
        yield test_client


@pytest.fixture
def blocked_client(tmp_path: Path) -> Iterator[TestClient]:
    profile = build_profile()
    services = build_pipeline_services(
        chunks_root=tmp_path / "chunks",
        embeddings_root=tmp_path / "embeddings",
        feature_flags=FeatureFlags(
            embedding_v2=True,
            indexing_bundle_first=True,
            retrieval_v1=True,
            rag_platform_v1=True,
            chatbot_webhook_v1=False,
        ),
        allow_mock_engine=True,
        seed_profiles=[profile],
        seed_targets=[build_target()],
        http_authenticator=_authenticator(),
    )
    app = create_app(services=services)
    app.state.rag_platform = FakeRagPlatformServices(_release())
    with TestClient(app) as test_client:
        test_client.headers.update(_auth_headers())
        yield test_client


@pytest.fixture
def unconfigured_webhook_client(tmp_path: Path) -> Iterator[TestClient]:
    profile = build_profile()
    chunk_bundle = write_chunk_bundle(
        tmp_path / "chunks",
        child_texts=DISTINCT_CHILD_TEXTS,
    )
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
    )
    app = create_app(services=services)
    app.state.test_profile = profile
    app.state.test_chunk_bundle = chunk_bundle
    app.state.rag_platform = FakeRagPlatformServices(_release())
    with TestClient(app) as test_client:
        test_client.headers.update(_auth_headers())
        yield test_client


def test_despacha_pregunta_y_chunks_al_webhook(client: TestClient) -> None:
    # `_activate_retrieval_profile` runs the LEGACY indexing activation flow only
    # to get vectors indexed for the fixture; its returned id belongs to a
    # different, unrelated `RetrievalProfile` (consumer_scope_id="sst-default")
    # than the one the release-scoped chatbot search actually uses.
    legacy_activation_profile_id = _activate_retrieval_profile(client)

    response = client.post(
        "/api/chatbot/questions",
        json={
            "project_id": PROJECT_ID,
            "rag_variant_id": RAG_VARIANT_ID,
            "rag_release_id": RAG_RELEASE_ID,
            "question": "safety rules",
            "conversation_id": "conv-1",
            "message_id": "msg-1",
            "top_k": 2,
        },
    )

    assert response.status_code == 202, response.text
    body = response.json()
    # PR-1 1.5: the reported id is the one that actually searched
    # (`chatbot.infrastructure.release_scoped_retrieval._release_profile`,
    # consumer_scope_id="release-scoped-dispatch"), never the coincidental id of
    # an unrelated legacy activation that only shares the same corpus/embedding
    # profile/indexing target.
    assert body["retrieval_profile_id"] != legacy_activation_profile_id
    assert body["retrieval_profile_id"].startswith("retrieval-profile-")
    assert body["question"] == "safety rules"
    assert body["chunks_sent"] == 2
    assert body["webhook_status_code"] == 202

    payload = client.app.state.test_webhook.payloads[0]
    assert payload.project_id == PROJECT_ID
    assert payload.rag_variant_id == RAG_VARIANT_ID
    assert payload.rag_release_id == RAG_RELEASE_ID
    # Used == reported: the webhook payload carries the exact same id as the HTTP
    # response -- both traced back to the single search that ran.
    assert payload.retrieval_profile_id == body["retrieval_profile_id"]
    assert payload.question == "safety rules"
    assert payload.conversation_id == "conv-1"
    assert payload.message_id == "msg-1"
    assert len(payload.chunks) == 2
    assert payload.chunks[0].document_id
    assert payload.chunks[0].document_name == "example.md"
    assert payload.chunks[0].child_chunk_id
    assert payload.chunks[0].text
    assert payload.chunks[0].metadata["document_name"] == "example.md"
    assert payload.chunks[0].metadata["citation_label"] == "example.md"
    assert (
        payload.chunks[0].metadata["answer_reference_phrase"]
        == "En el documento example.md se estipula"
    )


def test_despacha_release_publicada_sin_activar_la_lane_legacy(client: TestClient) -> None:
    indexing_run = _tag_release_context_without_legacy_activation(client)

    response = client.post(
        "/api/chatbot/questions",
        json={
            "project_id": PROJECT_ID,
            "rag_variant_id": RAG_VARIANT_ID,
            "rag_release_id": RAG_RELEASE_ID,
            "question": "warehouse floor evacuation",
            "top_k": 2,
        },
    )

    assert response.status_code == 202, response.text
    body = response.json()
    assert body["question"] == "warehouse floor evacuation"
    assert body["chunks_sent"] == 2

    payload = client.app.state.test_webhook.payloads[0]
    assert payload.rag_release_id == RAG_RELEASE_ID
    assert payload.retrieval_profile_id
    assert len(payload.chunks) == 2
    assert all(chunk.text for chunk in payload.chunks)
    # Regression guard: the release-scoped dispatch must not require the legacy
    # activation bit on the indexing run to become queryable.
    assert client.app.state.indexing_runs.get(indexing_run["run_id"]).activation_status == "pending"


def test_registra_eventos_estructurados_cuando_el_dispatch_es_exitoso(
    caplog: pytest.LogCaptureFixture,
    client: TestClient,
) -> None:
    _activate_retrieval_profile(client)
    caplog.set_level(logging.INFO)

    response = client.post(
        "/api/chatbot/questions",
        json={
            "project_id": PROJECT_ID,
            "rag_variant_id": RAG_VARIANT_ID,
            "rag_release_id": RAG_RELEASE_ID,
            "question": "safety rules",
            "top_k": 2,
        },
    )

    assert response.status_code == 202, response.text
    event_names = {
        record.event for record in caplog.records if hasattr(record, "event")
    }
    assert "chatbot_question_request_received" in event_names
    assert "chatbot_release_lane_resolved" in event_names
    assert "chatbot_evidence_retrieved" in event_names
    assert "chatbot_webhook_dispatch_completed" in event_names


def test_falla_cerrado_si_no_hay_perfil_activo_para_el_proyecto(client: TestClient) -> None:
    response = client.post(
        "/api/chatbot/questions",
        json={
            "project_id": PROJECT_ID,
            "rag_variant_id": RAG_VARIANT_ID,
            "rag_release_id": RAG_RELEASE_ID,
            "question": "safety rules",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CHATBOT_RELEASE_LANE_UNAVAILABLE"


def test_registra_evento_rechazado_cuando_el_release_no_corresponde_al_proyecto(
    caplog: pytest.LogCaptureFixture,
    client: TestClient,
) -> None:
    _activate_retrieval_profile(client)
    caplog.set_level(logging.INFO)

    response = client.post(
        "/api/chatbot/questions",
        json={
            "project_id": "proj_other",
            "rag_variant_id": RAG_VARIANT_ID,
            "rag_release_id": RAG_RELEASE_ID,
            "question": "safety rules",
        },
    )

    assert response.status_code == 409
    rejected = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "chatbot_question_request_rejected"
    ]
    assert rejected
    assert rejected[-1].attributes["reason"] == "release_project_mismatch"


def test_bloquea_el_endpoint_si_el_flag_esta_apagado(blocked_client: TestClient) -> None:
    response = blocked_client.post(
        "/api/chatbot/questions",
        json={
            "project_id": PROJECT_ID,
            "rag_variant_id": RAG_VARIANT_ID,
            "rag_release_id": RAG_RELEASE_ID,
            "question": "safety rules",
        },
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "CHATBOT_WEBHOOK_V1_DISABLED"


def test_bloquea_release_de_otro_proyecto(client: TestClient) -> None:
    _activate_retrieval_profile(client)

    response = client.post(
        "/api/chatbot/questions",
        json={
            "project_id": "proj_other",
            "rag_variant_id": RAG_VARIANT_ID,
            "rag_release_id": RAG_RELEASE_ID,
            "question": "safety rules",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CHATBOT_RAG_CONTEXT_MISMATCH"


def test_bloquea_release_de_otra_variante(client: TestClient) -> None:
    _activate_retrieval_profile(client)

    response = client.post(
        "/api/chatbot/questions",
        json={
            "project_id": PROJECT_ID,
            "rag_variant_id": "ragv_other",
            "rag_release_id": RAG_RELEASE_ID,
            "question": "safety rules",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CHATBOT_RAG_CONTEXT_MISMATCH"


def test_falla_cerrado_si_no_hay_webhook_configurado(
    caplog: pytest.LogCaptureFixture,
    unconfigured_webhook_client: TestClient,
) -> None:
    _activate_retrieval_profile(unconfigured_webhook_client)
    caplog.set_level(logging.INFO)

    response = unconfigured_webhook_client.post(
        "/api/chatbot/questions",
        json={
            "project_id": PROJECT_ID,
            "rag_variant_id": RAG_VARIANT_ID,
            "rag_release_id": RAG_RELEASE_ID,
            "question": "safety rules",
        },
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "CHATBOT_WEBHOOK_NOT_CONFIGURED"
    failed = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "chatbot_webhook_dispatch_failed"
    ]
    assert failed
    assert failed[-1].attributes["error_code"] == "CHATBOT_WEBHOOK_NOT_CONFIGURED"


# --------------------------------------------------------------------------- #
# GET /api/chatbot/rag-releases                                               #
# --------------------------------------------------------------------------- #

RAG_RELEASE_PUBLISHED_ID = "ragr_published"
RAG_RELEASE_DRAFT_ID = "ragr_draft"
RAG_RELEASE_OTHER_VARIANT_ID = "ragr_other-variant"
RAG_RELEASE_OTHER_PROJECT_ID = "ragr_other-project"
OTHER_VARIANT_ID = "ragv_other"
OTHER_PROJECT_ID = "proj_other"

#: Admin-only fields that must never leak through the narrow chatbot shape.
_PLATFORM_ADMIN_ONLY_FIELDS = frozenset(
    {
        "corpus_snapshot_id",
        "target_binding_key",
        "configuration_version",
        "release_manifest_hash",
        "created_by",
        "reason",
    }
)


def _rag_releases_app(tmp_path: Path):
    profile = build_profile()
    releases = (
        _release(
            rag_release_id=RAG_RELEASE_PUBLISHED_ID,
            release_number=2,
            state=ReleaseState.PUBLISHED,
        ),
        _release(
            rag_release_id=RAG_RELEASE_DRAFT_ID,
            release_number=3,
            state=ReleaseState.DRAFT,
        ),
        _release(
            rag_release_id=RAG_RELEASE_OTHER_VARIANT_ID,
            rag_variant_id=OTHER_VARIANT_ID,
            release_number=1,
            state=ReleaseState.PUBLISHED,
        ),
        _release(
            rag_release_id=RAG_RELEASE_OTHER_PROJECT_ID,
            project_id=OTHER_PROJECT_ID,
            release_number=1,
            state=ReleaseState.PUBLISHED,
        ),
    )
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
        http_authenticator=_authenticator(),
    )
    app = create_app(services=services)
    app.state.rag_platform = FakeRagPlatformServices(releases[0], releases=releases)
    return app


@pytest.fixture
def rag_releases_client(tmp_path: Path) -> Iterator[TestClient]:
    app = _rag_releases_app(tmp_path)
    with TestClient(app) as test_client:
        test_client.headers.update(_auth_headers())
        yield test_client


@pytest.fixture
def unauthenticated_rag_releases_client(tmp_path: Path) -> Iterator[TestClient]:
    app = _rag_releases_app(tmp_path)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def platform_disabled_client(tmp_path: Path) -> Iterator[TestClient]:
    profile = build_profile()
    services = build_pipeline_services(
        chunks_root=tmp_path / "chunks",
        embeddings_root=tmp_path / "embeddings",
        feature_flags=FeatureFlags(
            embedding_v2=True,
            indexing_bundle_first=True,
            retrieval_v1=True,
            rag_platform_v1=False,
            chatbot_webhook_v1=True,
        ),
        allow_mock_engine=True,
        seed_profiles=[profile],
        seed_targets=[build_target()],
        http_authenticator=_authenticator(),
    )
    app = create_app(services=services)
    with TestClient(app) as test_client:
        test_client.headers.update(_auth_headers())
        yield test_client


def test_lista_releases_del_proyecto_con_forma_estrecha(
    rag_releases_client: TestClient,
) -> None:
    response = rag_releases_client.get(
        "/api/chatbot/rag-releases", params={"project_id": PROJECT_ID}
    )

    assert response.status_code == 200, response.text
    body = response.json()
    returned_ids = {item["rag_release_id"] for item in body["items"]}
    assert returned_ids == {
        RAG_RELEASE_PUBLISHED_ID,
        RAG_RELEASE_DRAFT_ID,
        RAG_RELEASE_OTHER_VARIANT_ID,
    }
    assert body["total_items"] == 3
    for item in body["items"]:
        assert item["project_id"] == PROJECT_ID
        assert set(item) == {
            "rag_release_id",
            "project_id",
            "rag_variant_id",
            "state",
            "release_number",
            "created_at",
            "validated_at",
        }
        assert _PLATFORM_ADMIN_ONLY_FIELDS.isdisjoint(item)


def test_filtra_releases_por_rag_variant_id(rag_releases_client: TestClient) -> None:
    response = rag_releases_client.get(
        "/api/chatbot/rag-releases",
        params={"project_id": PROJECT_ID, "rag_variant_id": RAG_VARIANT_ID},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    returned_ids = {item["rag_release_id"] for item in body["items"]}
    assert returned_ids == {RAG_RELEASE_PUBLISHED_ID, RAG_RELEASE_DRAFT_ID}
    assert all(item["rag_variant_id"] == RAG_VARIANT_ID for item in body["items"])


def test_devuelve_vacio_cuando_el_proyecto_es_desconocido(
    rag_releases_client: TestClient,
) -> None:
    response = rag_releases_client.get(
        "/api/chatbot/rag-releases", params={"project_id": "proj_no-existe"}
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["items"] == []
    assert body["total_items"] == 0


def test_rechaza_project_id_vacio(rag_releases_client: TestClient) -> None:
    response = rag_releases_client.get(
        "/api/chatbot/rag-releases", params={"project_id": ""}
    )

    assert response.status_code == 422


def test_exige_bearer_token_para_listar_releases(
    unauthenticated_rag_releases_client: TestClient,
) -> None:
    response = unauthenticated_rag_releases_client.get(
        "/api/chatbot/rag-releases", params={"project_id": PROJECT_ID}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "HTTP_AUTH_REQUIRED"


def test_rechaza_bearer_token_invalido_para_listar_releases(
    unauthenticated_rag_releases_client: TestClient,
) -> None:
    response = unauthenticated_rag_releases_client.get(
        "/api/chatbot/rag-releases",
        params={"project_id": PROJECT_ID},
        headers=_auth_headers("token-que-no-existe"),
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "HTTP_AUTH_INVALID_CREDENTIALS"


def test_bloquea_listado_de_releases_si_el_flag_esta_apagado(
    platform_disabled_client: TestClient,
) -> None:
    response = platform_disabled_client.get(
        "/api/chatbot/rag-releases", params={"project_id": PROJECT_ID}
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "RAG_PLATFORM_V1_DISABLED"
