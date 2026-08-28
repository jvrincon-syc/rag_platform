"""BGE-M3 cross-score reranker: real relevance judgment over the deduped pool.

Fusion (RRF) only knows rank position per lane, never how relevant a
candidate's actual text is to the query -- that's why weak-lexical cases
can't be told apart from strong ones by tuning fusion constants (see
``retrieval/fusion.py``). ``BGEM3FlagModel.compute_score`` judges query and
passage text directly with the same model already used for retrieval
embeddings; no new dependency (FlagEmbedding is already required for the bge
embedding provider, see ``indexing/infrastructure/embeddings/bge.py``).

When the composition root passes a shared ``BgeModelCache`` (same one given to
``BgeEmbeddingProvider``), this reranker reuses the exact same loaded weights
instead of loading its own ~2GB copy: a cold first request previously paid two
sequential BGE-M3 loads (~13s each) because the embedding provider and this
reranker were unaware of each other. Without a cache (tests, or callers that
never wire one) it falls back to loading its own instance, unchanged from
before.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable, Protocol

from indexing.infrastructure.embeddings.bge import BgeModelCache
from retrieval.domain.models import RetrievedEvidence


class BgeScoringModel(Protocol):
    def compute_score(self, pairs: list[list[str]], **kwargs: object) -> object:
        """Score query/passage pairs (FlagEmbedding ``BGEM3FlagModel`` API)."""


BgeRerankerModelLoader = Callable[[], BgeScoringModel]

#: dense, sparse, colbert -- BGE-M3's own combined-score weighting.
_DEFAULT_WEIGHTS: tuple[float, float, float] = (0.4, 0.2, 0.4)


@dataclass
class BgeReranker:
    """Reorders a deduped candidate pool by BGE-M3's combined relevance score."""

    model_name: str = "BAAI/bge-m3"
    weights: tuple[float, float, float] = _DEFAULT_WEIGHTS
    model_loader: BgeRerankerModelLoader | None = None
    model_cache: BgeModelCache | None = None
    _model: BgeScoringModel | None = field(default=None, init=False, repr=False)

    def rerank(
        self, *, query: str, candidates: list[RetrievedEvidence], top_n: int
    ) -> list[RetrievedEvidence]:
        if not candidates:
            return []
        model = self._get_model()
        pairs = [[query, candidate.text] for candidate in candidates]
        raw = model.compute_score(pairs, weights_for_different_modes=list(self.weights))
        scores = raw["colbert+sparse+dense"] if isinstance(raw, dict) else raw
        ranked = sorted(zip(candidates, scores), key=lambda pair: pair[1], reverse=True)
        return [
            candidate.model_copy(
                update={
                    "score": float(score),
                    "metadata": {
                        **candidate.metadata,
                        "rerank_score": float(score),
                        "pre_rerank_score": candidate.score,
                    },
                }
            )
            for candidate, score in ranked[:top_n]
        ]

    def _get_model(self) -> BgeScoringModel:
        if self._model is None:
            loader = self.model_loader if self.model_loader is not None else self._load_model
            self._model = (
                self.model_cache.get_or_load(self.model_name, loader)
                if self.model_cache is not None
                else loader()
            )
        return self._model

    def _load_model(self) -> BgeScoringModel:
        # HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE cached module-level at
        # transformers/huggingface_hub's OWN import time; must be set
        # before `from FlagEmbedding import ...` (which imports them
        # transitively), else too late (same gotcha fixed in
        # indexing/infrastructure/embeddings/bge.py::_load_bge_model).
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        try:
            from FlagEmbedding import BGEM3FlagModel
        except ImportError as error:
            raise RuntimeError(
                "FlagEmbedding is required for the bge reranker"
            ) from error
        return BGEM3FlagModel(self.model_name, use_fp16=False)
