from __future__ import annotations

from chatbot_runtime.warmup import BgeWarmupService


class _EmbeddingProbeError(RuntimeError):
    pass


class _RerankerProbeError(RuntimeError):
    pass


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


def test_warmup_falla_cerrado_y_omite_reranking_si_falla_embedding() -> None:
    called: list[str] = []

    def fail_embedding() -> None:
        called.append("embed")
        raise _EmbeddingProbeError("secret provider path")

    def rerank_probe() -> None:
        called.append("rerank")

    service = BgeWarmupService(
        embed_probe=fail_embedding,
        rerank_probe=rerank_probe,
    )

    status = service.warm()

    assert called == ["embed"]
    assert status.ready is False
    assert service.ready() is False
    assert status.warmed_embedding is False
    assert status.warmed_reranker is False
    assert status.last_error == "_EmbeddingProbeError"
    assert "secret provider path" not in (status.last_error or "")


def test_warmup_falla_cerrado_y_conserva_embedding_si_falla_reranking() -> None:
    called: list[str] = []

    def embed_probe() -> None:
        called.append("embed")

    def fail_reranking() -> None:
        called.append("rerank")
        raise _RerankerProbeError("secret provider response")

    service = BgeWarmupService(
        embed_probe=embed_probe,
        rerank_probe=fail_reranking,
    )

    status = service.warm()

    assert called == ["embed", "rerank"]
    assert status.ready is False
    assert service.ready() is False
    assert status.warmed_embedding is True
    assert status.warmed_reranker is False
    assert status.last_error == "_RerankerProbeError"
    assert "secret provider response" not in (status.last_error or "")
