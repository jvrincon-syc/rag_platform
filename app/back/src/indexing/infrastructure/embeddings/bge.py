from __future__ import annotations

from dataclasses import dataclass
import logging
import os
import threading
from typing import Callable, Protocol

from indexing.application.embedding_provider import (
    EmbeddingBatch,
    EmbeddingCapabilities,
    EmbeddingProviderConfigurationError,
)
from indexing.domain.models import IndexingProfile
from indexing.domain.profiles import DistanceMetric
from indexing.infrastructure.embeddings.base import embedding_batch, validate_texts
from indexing.infrastructure.embeddings.settings import EmbeddingSettings


class EmbeddingProviderUnavailableError(RuntimeError):
    """Embedding provider runtime is not configured."""


class BgeRuntimeModel(Protocol):
    def encode(self, texts, **kwargs):
        """Encode texts with FlagEmbedding."""


BgeModelLoader = Callable[[EmbeddingSettings], BgeRuntimeModel]
logger = logging.getLogger(__name__)


class BgeModelCache:
    """Process-wide cache of loaded BGE runtimes, keyed by Hugging Face model name.

    ``BGEM3FlagModel`` weighs ~2GB and takes ~10-15s to load cold; the embedding
    provider (dense/sparse encode) and the reranker (colbert+sparse+dense score)
    are separate adapters that both need the exact same weights when they name
    the same model. Without this cache each adapter loads its own instance,
    doubling both load latency and memory. This cache is injected explicitly by
    the composition root into every adapter that needs a BGE runtime -- it is
    not reached for globally, so it stays a constructor-injected collaborator,
    not a service locator.
    """

    def __init__(self) -> None:
        self._models: dict[str, object] = {}
        self._lock = threading.Lock()

    def get_or_load(self, model_name: str, loader: Callable[[], object]) -> object:
        """Return the cached runtime for ``model_name``, loading it at most once."""

        with self._lock:
            model = self._models.get(model_name)
            if model is None:
                model = loader()
                self._models[model_name] = model
            return model


@dataclass
class BgeEmbeddingProvider:
    profile: IndexingProfile
    settings: EmbeddingSettings | None = None
    model_loader: BgeModelLoader | None = None
    model_cache: BgeModelCache | None = None

    def __post_init__(self) -> None:
        self._settings = self.settings or EmbeddingSettings(provider="bge")
        self._model: BgeRuntimeModel | None = None

    @property
    def provider_name(self) -> str:
        return self.profile.embedding_provider

    @property
    def model_name(self) -> str:
        return self.profile.embedding_model

    @property
    def dimension(self) -> int:
        return self.profile.embedding_dimension

    @property
    def distance_metric(self) -> DistanceMetric:
        return self._settings.distance_metric

    @property
    def normalized(self) -> bool:
        return True

    @property
    def capabilities(self) -> EmbeddingCapabilities:
        return EmbeddingCapabilities(supports_sparse=True, supports_multimodal=False)

    @property
    def batch_size(self) -> int:
        return self._settings.batch_size

    @property
    def retries(self) -> int:
        return 0

    def embed_documents(self, texts: list[str]) -> EmbeddingBatch:
        return self._embed(
            texts,
            method_name="encode_corpus",
            max_length=self._settings.bge_document_max_length,
        )

    def embed_queries(self, texts: list[str]) -> EmbeddingBatch:
        return self._embed(
            texts,
            method_name="encode_queries",
            max_length=self._settings.bge_query_max_length,
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self.embed_documents(texts).vectors

    def _embed(
        self,
        texts: list[str],
        *,
        method_name: str,
        max_length: int,
    ) -> EmbeddingBatch:
        batch_texts = validate_texts(texts)
        model = self._get_model()
        method = getattr(model, method_name, None)
        if method is None:
            method = model.encode
        logger.debug(
            "embedding bge batch started",
            extra={
                "provider": self.provider_name,
                "model": self.model_name,
                "method": method_name,
                "text_count": len(batch_texts),
                "batch_size": self._settings.batch_size,
                "max_length": max_length,
            },
        )
        vectors: list[list[float]] = []
        for chunk in _chunks(batch_texts, self._settings.batch_size):
            output = method(
                chunk,
                batch_size=self._settings.batch_size,
                max_length=max_length,
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False,
            )
            chunk_vectors = output.get("dense_vecs") if isinstance(output, dict) else output
            vectors.extend(chunk_vectors)
        batch = embedding_batch(
            vectors=vectors,
            expected_count=len(batch_texts),
            profile=self.profile,
            distance_metric=self.distance_metric,
            normalized=self.normalized,
            capabilities=self.capabilities,
        )
        logger.debug(
            "embedding bge batch completed",
            extra={
                "provider": batch.provider,
                "model": batch.model,
                "method": method_name,
                "vector_count": len(batch.vectors),
                "dimension": batch.dimension,
            },
        )
        return batch

    def _get_model(self) -> BgeRuntimeModel:
        if self._model is None:
            logger.info(
                "loading bge embedding runtime",
                extra={
                    "provider": self.provider_name,
                    "model": self.model_name,
                    "device": self._settings.device,
                    "batch_size": self._settings.batch_size,
                    "shared_cache": self.model_cache is not None,
                },
            )
            loader: Callable[[], BgeRuntimeModel] = lambda: (
                self.model_loader(self._settings)
                if self.model_loader is not None
                else _load_bge_model(self.profile, self._settings)
            )
            self._model = (
                self.model_cache.get_or_load(self.model_name, loader)
                if self.model_cache is not None
                else loader()
            )
        return self._model


def _load_bge_model(
    profile: IndexingProfile,
    settings: EmbeddingSettings,
) -> BgeRuntimeModel:
    # transformers/huggingface_hub cache HF_HUB_OFFLINE as a module-level
    # constant read at THEIR OWN import time; setting it after importing
    # FlagEmbedding (which imports them transitively) is too late. Must run
    # before that import, every time -- on a box with no reliable route to
    # huggingface.co this otherwise hangs for minutes on a chat-template
    # listing call and fails the whole embedding run, even with the model
    # already fully cached locally (live symptom: httpx.ConnectTimeout deep
    # inside AutoTokenizer.from_pretrained during a real release build).
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    try:
        from FlagEmbedding import BGEM3FlagModel
    except ImportError as error:
        raise EmbeddingProviderConfigurationError(
            "FlagEmbedding is required for the bge embedding provider"
        ) from error
    use_fp16 = settings.bge_use_fp16 and settings.device.lower().startswith("cuda")
    kwargs: dict[str, object] = {"use_fp16": use_fp16}
    if settings.device:
        kwargs["devices"] = settings.device
    if settings.hf_hub_cache:
        kwargs["cache_dir"] = settings.hf_hub_cache
    return BGEM3FlagModel(profile.embedding_model, **kwargs)


def _chunks(texts: list[str], batch_size: int) -> list[list[str]]:
    return [
        texts[index : index + batch_size]
        for index in range(0, len(texts), batch_size)
    ]
