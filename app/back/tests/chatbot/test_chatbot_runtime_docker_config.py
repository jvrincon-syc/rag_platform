from __future__ import annotations

from pathlib import Path


def test_dockerfile_declares_runtime_entrypoints_and_embeddings_install() -> None:
    dockerfile = Path("app/back/Dockerfile").read_text(encoding="utf-8")

    assert "api-entrypoint.sh" in dockerfile
    assert "worker-entrypoint.sh" in dockerfile
    assert "pip install .[embeddings]" in dockerfile
    assert "curl" in dockerfile


def test_compose_wires_api_and_worker_with_shared_hf_cache() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "rag-platform-api:" in compose
    assert "rag-platform-worker:" in compose
    assert "rag-platform-hf-cache" in compose
    assert "/var/lib/rag_platform/hf-cache" in compose
    assert "CHATBOT_RUNTIME_CHUNKS_ROOT" in compose
    assert "CHATBOT_RUNTIME_EMBEDDINGS_ROOT" in compose
    assert "service_healthy" in compose


def test_worker_entrypoint_executes_runtime_warmup_loop() -> None:
    script = Path("app/back/docker/worker-entrypoint.sh").read_text(encoding="utf-8")

    assert "python -m chatbot_runtime.warmup" in script
    assert "CHATBOT_RUNTIME_WARM_INTERVAL_SECONDS" in script
    assert "chatbot-runtime-worker-ready" in script
