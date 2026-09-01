"""Lightweight cross-encoder reranker (bge-reranker-base) as a fast alternative to
BGE-M3's colbert+sparse+dense ``compute_score``.

BGE-M3 reranking on CPU costs ~2s per candidate because it scores three heads
(colbert token-level MaxSim dominates). ``bge-reranker-base`` is a single
cross-encoder head: measured ~4.6x faster on the same pool, with ~3/4 top-4
agreement. It is opt-in (``RETRIEVAL_RERANKER=light``); the default stays BGE-M3
so quality never changes silently. Same ``RerankerPort`` contract as
``BgeReranker``; swap one for the other at the composition root.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable, Protocol

from retrieval.domain.models import RetrievedEvidence


class CrossEncoderScorer(Protocol):
    def compute_score(self, pairs: list[list[str]], **kwargs: object) -> object:
        """Score query/passage pairs (FlagEmbedding ``FlagReranker`` API)."""


@dataclass
class LightCrossEncoderReranker:
    """Reorders a deduped candidate pool by a single cross-encoder's relevance score."""

    model_name: str = "BAAI/bge-reranker-base"
    model_loader: Callable[[], CrossEncoderScorer] | None = None
    _model: CrossEncoderScorer | None = field(default=None, init=False, repr=False)

    def rerank(
        self, *, query: str, candidates: list[RetrievedEvidence], top_n: int
    ) -> list[RetrievedEvidence]:
        if not candidates:
            return []
        model = self._get_model()
        pairs = [[query, candidate.text] for candidate in candidates]
        raw = model.compute_score(pairs)
        # FlagReranker returns a float for one pair, a list for many; normalize to list.
        scores = raw if isinstance(raw, list) else [raw]
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

    def warm(self) -> None:
        """Force the model load now so the first real request pays no cold load."""

        self._get_model()

    def _get_model(self) -> CrossEncoderScorer:
        if self._model is None:
            loader = self.model_loader if self.model_loader is not None else self._load_model
            self._model = loader()
        return self._model

    def _load_model(self) -> CrossEncoderScorer:
        # Same offline gotcha as bge.py: set before importing FlagEmbedding (which
        # imports transformers/huggingface_hub transitively).
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        try:
            from FlagEmbedding import FlagReranker
        except ImportError as error:
            raise RuntimeError(
                "FlagEmbedding is required for the light cross-encoder reranker"
            ) from error
        # Load from the explicit local snapshot dir, not the repo id: models pulled with
        # huggingface_hub 1.x land in the Xet cache layout that an older hub can't resolve
        # by name (it then tries the network and fails offline). A direct dir path loads
        # via transformers' local-path branch, bypassing hub resolution entirely.
        return FlagReranker(_resolve_local_snapshot(self.model_name), use_fp16=False)


def _resolve_local_snapshot(model_name: str) -> str:
    """Return the local HF-cache snapshot dir for ``model_name``, or the name unchanged.

    Falls back to the repo id when the model is not cached (e.g. a networked host that
    can resolve it normally), so behaviour is unchanged where hub resolution works.
    """

    import glob

    repo = "models--" + model_name.replace("/", "--")
    pattern = os.path.expanduser(f"~/.cache/huggingface/hub/{repo}/snapshots/*/")
    snapshots = glob.glob(pattern)
    return snapshots[0] if snapshots else model_name
