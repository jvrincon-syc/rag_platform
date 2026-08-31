from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from fastapi.testclient import TestClient

from chatbot_runtime.app import build_chatbot_runtime
from chatbot_runtime.warmup import BgeWarmupService
from core.http_auth import AUTH_CREDENTIALS_JSON_KEY


def _runtime_env() -> Mapping[str, str]:
    return {
        "SST_PERSISTENCE_MODE": "memory",
        AUTH_CREDENTIALS_JSON_KEY: '[{"principal_id":"runtime","token":"test-token"}]',
    }


def _stub_warmup(*, ready: bool) -> BgeWarmupService:
    service = BgeWarmupService(
        embed_probe=lambda: None,
        rerank_probe=lambda: None,
    )
    if ready:
        service.warm()
    return service


def test_runtime_expone_health_y_readiness_separados(tmp_path: Path) -> None:
    runtime = build_chatbot_runtime(
        chunks_root=tmp_path / "chunks",
        embeddings_root=tmp_path / "embeddings",
        environ=_runtime_env(),
        warmup_service=_stub_warmup(ready=False),
    )
    client = TestClient(runtime.app)

    assert client.get("/healthz").status_code == 200
    readiness = client.get("/readyz")
    assert readiness.status_code == 503
    assert readiness.json()["ready"] is False


def test_runtime_reporta_ready_cuando_bge_ya_esta_warm(tmp_path: Path) -> None:
    runtime = build_chatbot_runtime(
        chunks_root=tmp_path / "chunks",
        embeddings_root=tmp_path / "embeddings",
        environ=_runtime_env(),
        warmup_service=_stub_warmup(ready=True),
    )
    client = TestClient(runtime.app)

    readiness = client.get("/readyz")
    assert readiness.status_code == 200
    assert readiness.json()["ready"] is True


def test_runtime_mount_preserves_chatbot_route_contract(tmp_path: Path) -> None:
    runtime = build_chatbot_runtime(
        chunks_root=tmp_path / "chunks",
        embeddings_root=tmp_path / "embeddings",
        environ=_runtime_env(),
        warmup_service=_stub_warmup(ready=True),
    )
    client = TestClient(runtime.app)

    response = client.post("/api/chatbot/questions", json={"question": "Hola"})

    assert response.status_code in {400, 401, 422}
