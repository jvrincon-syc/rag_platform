"""Unit tests for the BGE-M3 reranker adapter, using a fake scoring model.

No FlagEmbedding import, no network, no real weights -- see
``test_bge_reranker_live.py`` for the ``bge_runtime``-marked live smoke test.
"""

from __future__ import annotations

from indexing.domain.models import IndexingProfile
from indexing.infrastructure.embeddings.bge import BgeEmbeddingProvider, BgeModelCache
from indexing.infrastructure.embeddings.settings import EmbeddingSettings
from retrieval.domain.models import RetrievedEvidence
from retrieval.infrastructure.bge_reranker import BgeReranker


def _evidence(node_id: str, *, text: str) -> RetrievedEvidence:
    return RetrievedEvidence(
        node_id=node_id,
        document_id=f"doc-{node_id}",
        child_chunk_id=node_id,
        text=text,
        score=0.0,
        source="vector",
        embedding_profile_id="local-bge-m3-v1",
        corpus_version="corpus-v1",
    )


class FakeScoringModel:
    def __init__(self) -> None:
        self.calls: list[list[list[str]]] = []

    def compute_score(self, pairs, **kwargs):
        self.calls.append(pairs)
        # First pair scores lower than the second so ranking is observable.
        return {"colbert+sparse+dense": [0.1 * (index + 1) for index in range(len(pairs))]}


def test_rerank_reorders_candidates_by_descending_score() -> None:
    fake_model = FakeScoringModel()
    reranker = BgeReranker(model_loader=lambda: fake_model)
    low = _evidence("low", text="unrelated passage")
    high = _evidence("high", text="literal answer")

    result = reranker.rerank(query="question", candidates=[low, high], top_n=2)

    assert [item.node_id for item in result] == ["high", "low"]
    assert result[0].metadata["rerank_score"] == 0.2
    assert len(fake_model.calls) == 1


def test_rerank_no_op_cuando_no_hay_candidatos() -> None:
    reranker = BgeReranker(model_loader=lambda: FakeScoringModel())

    assert reranker.rerank(query="question", candidates=[], top_n=5) == []


def _profile(*, model: str) -> IndexingProfile:
    return IndexingProfile(
        profile_id="bge-profile",
        chunking_version="structure-aware-v1",
        embedding_provider="bge",
        embedding_model=model,
        embedding_dimension=3,
        vector_store="memory",
        metadata_schema_version="2.0",
    )


def test_reranker_reusa_el_modelo_ya_cargado_por_el_embedding_provider_cuando_comparten_cache() -> None:
    """Reproduces the reported double-load: same model name, shared cache -> one load."""

    load_calls: list[str] = []

    def loader() -> object:
        load_calls.append("loaded")
        return FakeSharedModel()

    shared_cache = BgeModelCache()
    provider = BgeEmbeddingProvider(
        profile=_profile(model="BAAI/bge-m3"),
        settings=EmbeddingSettings(provider="bge"),
        model_loader=lambda _settings: loader(),
        model_cache=shared_cache,
    )
    reranker = BgeReranker(
        model_name="BAAI/bge-m3",
        model_loader=loader,
        model_cache=shared_cache,
    )

    provider.embed_documents(["doc uno"])
    reranker.rerank(
        query="q",
        candidates=[_evidence("n1", text="passage")],
        top_n=1,
    )

    assert load_calls == ["loaded"]


def test_reranker_carga_su_propio_modelo_cuando_no_hay_cache_compartido() -> None:
    """Without an injected cache, behavior is unchanged: each adapter loads its own."""

    load_calls: list[str] = []

    def loader() -> object:
        load_calls.append("loaded")
        return FakeSharedModel()

    provider = BgeEmbeddingProvider(
        profile=_profile(model="BAAI/bge-m3"),
        settings=EmbeddingSettings(provider="bge"),
        model_loader=lambda _settings: loader(),
    )
    reranker = BgeReranker(model_name="BAAI/bge-m3", model_loader=loader)

    provider.embed_documents(["doc uno"])
    reranker.rerank(
        query="q",
        candidates=[_evidence("n1", text="passage")],
        top_n=1,
    )

    assert load_calls == ["loaded", "loaded"]


class FakeSharedModel:
    """Serves both the embedding provider API and the reranker API."""

    def encode_corpus(self, texts, *, batch_size, max_length, **kwargs):
        return {"dense_vecs": [[1.0, 0.0, 0.0] for _ in texts]}

    def encode_queries(self, texts, *, batch_size, max_length, **kwargs):
        return {"dense_vecs": [[0.0, 1.0, 0.0] for _ in texts]}

    def compute_score(self, pairs, **kwargs):
        return {"colbert+sparse+dense": [0.5 for _ in pairs]}
