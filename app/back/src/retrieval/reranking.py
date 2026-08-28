from __future__ import annotations

from retrieval.domain.models import RetrievedEvidence


class NoOpReranker:
    """Default ``RerankerPort``: preserves fusion/dedup order, just cuts to top_n."""

    def rerank(
        self, *, query: str, candidates: list[RetrievedEvidence], top_n: int
    ) -> list[RetrievedEvidence]:
        return candidates[:top_n]
