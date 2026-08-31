from __future__ import annotations

from chatbot_runtime.warmup import BgeWarmupService


def test_readiness_false_antes_del_warmup() -> None:
    service = BgeWarmupService(
        embed_probe=lambda: None,
        rerank_probe=lambda: None,
    )

    status = service.status()

    assert status.ready is False
    assert status.warmed_embedding is False
    assert status.warmed_reranker is False


def test_readiness_true_despues_de_warmup_exitoso() -> None:
    called: list[str] = []
    service = BgeWarmupService(
        embed_probe=lambda: called.append("embed"),
        rerank_probe=lambda: called.append("rerank"),
    )

    status = service.warm()

    assert called == ["embed", "rerank"]
    assert status.ready is True
    assert status.warmed_embedding is True
    assert status.warmed_reranker is True
